"""Immutable, hash-verified evidence package generation."""
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import select

from backend.config import PROJECT_ROOT, settings
from backend.database import crud
from backend.database.models import EventModel
from backend.interpreter.timeline import build_timeline
from backend.models.event import event_dict


class EvidenceManager:
    def _path(self, incident_id: str) -> Path:
        if not incident_id.startswith("INC-") or any(token in incident_id for token in ("..", "/", "\\")):
            raise ValueError("invalid incident identifier")
        root = settings.evidence_dir.resolve()
        path = (root / f"incident_{incident_id}").resolve()
        if root not in path.parents:
            raise ValueError("evidence path escapes evidence directory")
        return path

    @staticmethod
    def _hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    async def preserve(self, session, incident_id: str, interpretation=None) -> str:
        folder = self._path(incident_id)
        if folder.exists():
            return str(folder)
        incident = await crud.get_incident_by_id(session, incident_id)
        if incident is None:
            raise ValueError(f"incident not found: {incident_id}")
        events = await crud.get_events_for_incident(session, incident_id)
        linked_ids = {event.event_id for event in events}
        context_seconds = max(0, int(settings.evidence_context_minutes)) * 60
        if events and context_seconds:
            timestamps = [event.timestamp.replace(tzinfo=timezone.utc) for event in events]
            lower = min(timestamps) - timedelta(seconds=context_seconds)
            upper = max(timestamps) + timedelta(seconds=context_seconds)
            events = list((await session.scalars(
                select(EventModel)
                .where(EventModel.timestamp >= lower, EventModel.timestamp <= upper)
                .order_by(EventModel.timestamp)
            )).all())
        snapshot = await crud.get_latest_system_snapshot(session)
        event_payload = [{**event_dict(event), "linked_to_incident": event.event_id in linked_ids} for event in events]
        timeline = {"incident_id": incident_id, "events": build_timeline(events), "interpretation": interpretation or {}}
        system = {} if snapshot is None else {"hostname": snapshot.hostname, "os_name": snapshot.os_name, "os_version": snapshot.os_version, "captured_at": snapshot.captured_at.isoformat(), "uptime_seconds": snapshot.uptime_seconds, "boot_time": (snapshot.captured_at - timedelta(seconds=snapshot.uptime_seconds)).isoformat() if snapshot.uptime_seconds is not None else None}
        payloads = {
            "events.json": event_payload,
            "timeline.json": timeline,
            "system_info.json": system,
            "README.txt": f"DFIR evidence package for {incident_id}. Preserve this package and verify manifest hashes before use. Automated findings require human verification.\n",
        }
        folder.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{folder.name}.", dir=folder.parent))
        try:
            for name, payload in payloads.items():
                (temporary / name).write_text(payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str), encoding="utf-8")
            manifest = {"incident_id": incident_id, "created_at": datetime.now(timezone.utc).isoformat(), "files": {}}
            for name in payloads:
                file_path = temporary / name
                manifest["files"][name] = {"sha256": self._hash(file_path), "size_bytes": file_path.stat().st_size}
            (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            temporary.replace(folder)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        incident.evidence_path = str(folder.relative_to(PROJECT_ROOT))
        await session.commit()
        return str(folder)

    def get_manifest(self, incident_id: str) -> dict:
        return json.loads((self._path(incident_id) / "manifest.json").read_text(encoding="utf-8"))

    def verify(self, incident_id: str) -> dict:
        folder = self._path(incident_id)
        try:
            manifest = self.get_manifest(incident_id)
        except (OSError, json.JSONDecodeError) as exc:
            return {"incident_id": incident_id, "valid": False, "missing": ["manifest.json"], "unexpected": [], "files": {}, "error": str(exc)}
        required_names = {"events.json", "timeline.json", "system_info.json", "README.txt"}
        entries = manifest.get("files", {})
        if set(entries) != required_names or manifest.get("incident_id") != incident_id:
            raise ValueError("evidence manifest has an invalid file set or incident identifier")
        files = {}
        for name, expected in entries.items():
            if Path(name).name != name or name in {".", ".."}:
                raise ValueError("evidence manifest contains an unsafe path")
            path = folder / name
            actual = self._hash(path) if path.is_file() else None
            size = path.stat().st_size if path.is_file() else None
            files[name] = {"valid": actual == expected.get("sha256") and size == expected.get("size_bytes"), "expected": expected.get("sha256"), "actual": actual, "expected_size_bytes": expected.get("size_bytes"), "actual_size_bytes": size}
        actual_names = {item.name for item in folder.iterdir() if item.is_file()} - {"manifest.json"}
        unexpected = sorted(actual_names - required_names)
        missing = sorted(required_names - actual_names)
        for name in unexpected:
            files[name] = {"valid": False, "unexpected": True}
        return {"incident_id": incident_id, "valid": not missing and not unexpected and all(item["valid"] for item in files.values()), "missing": missing, "unexpected": unexpected, "files": files}

    def zip(self, incident_id: str) -> str:
        folder = self._path(incident_id)
        return shutil.make_archive(str(folder), "zip", folder)
