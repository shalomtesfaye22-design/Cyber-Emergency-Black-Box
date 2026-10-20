"""Immutable, hash-verified evidence package generation."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from backend.config import PROJECT_ROOT, settings
from backend.database import crud
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
        folder.mkdir(parents=True, exist_ok=False)
        incident = await crud.get_incident_by_id(session, incident_id)
        events = await crud.get_events_for_incident(session, incident_id)
        snapshot = await crud.get_latest_system_snapshot(session)
        event_payload = [event_dict(event) for event in events]
        timeline = {"incident_id": incident_id, "events": build_timeline(events), "interpretation": interpretation or {}}
        system = {} if snapshot is None else {"hostname": snapshot.hostname, "os_name": snapshot.os_name, "os_version": snapshot.os_version, "captured_at": snapshot.captured_at.isoformat(), "uptime_seconds": snapshot.uptime_seconds}
        payloads = {
            "events.json": event_payload,
            "timeline.json": timeline,
            "system_info.json": system,
            "README.txt": f"DFIR evidence package for {incident_id}. Preserve this package and verify manifest hashes before use. Automated findings require human verification.\n",
        }
        for name, payload in payloads.items():
            (folder / name).write_text(payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str), encoding="utf-8")
        manifest = {"incident_id": incident_id, "created_at": datetime.now(timezone.utc).isoformat(), "files": {}}
        for name in payloads:
            file_path = folder / name
            manifest["files"][name] = {"sha256": self._hash(file_path), "size_bytes": file_path.stat().st_size}
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        incident.evidence_path = str(folder.relative_to(PROJECT_ROOT))
        await session.commit()
        return str(folder)

    def get_manifest(self, incident_id: str) -> dict:
        return json.loads((self._path(incident_id) / "manifest.json").read_text(encoding="utf-8"))

    def verify(self, incident_id: str) -> dict:
        folder, manifest = self._path(incident_id), self.get_manifest(incident_id)
        files = {}
        for name, expected in manifest["files"].items():
            path = folder / name
            actual = self._hash(path) if path.is_file() else None
            files[name] = {"valid": actual == expected["sha256"], "expected": expected["sha256"], "actual": actual}
        return {"incident_id": incident_id, "valid": all(item["valid"] for item in files.values()), "files": files}

    def zip(self, incident_id: str) -> str:
        folder = self._path(incident_id)
        return shutil.make_archive(str(folder), "zip", folder)
