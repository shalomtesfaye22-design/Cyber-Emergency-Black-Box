import shutil
from datetime import datetime, timezone
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import crud
from backend.evidence.manager import EvidenceManager


def test_evidence_rejects_path_traversal():
    mgr = EvidenceManager()
    with pytest.raises(ValueError):
        mgr._path("../../../bad")
    with pytest.raises(ValueError):
        mgr._path("INC-../../../etc/passwd")
    with pytest.raises(ValueError):
        mgr._path("INC-test\\..\\evil")
    with pytest.raises(ValueError):
        mgr._path("BAD-PREFIX-001")


@pytest.mark.asyncio
async def test_evidence_preserve_verify_and_zip(db_session: AsyncSession):
    mgr = EvidenceManager()
    incident_id = "INC-TEST-EV-001"
    now = datetime.now(timezone.utc)

    # Insert test incident and event
    await crud.insert_incident(
        db_session,
        {
            "incident_id": incident_id,
            "detection_time": now,
            "rule_id": "R-TEST",
            "rule_name": "Test Evidence Rule",
            "severity": "HIGH",
            "status": "OPEN",
            "summary": "Evidence package test",
            "event_count": 1,
        },
    )
    await crud.insert_event(
        db_session,
        {
            "event_id": "ev-item-01",
            "timestamp": now,
            "event_type": "login_failure",
            "source": "evidence_test",
            "user_name": "eve",
            "preserved": False,
        },
    )
    await crud.link_events_to_incident(db_session, incident_id, ["ev-item-01"])

    folder_path = None
    zip_path = None
    try:
        # Preserve evidence package
        preservation_result = await mgr.preserve(db_session, incident_id)
        folder = Path(preservation_result)
        folder_path = folder
        assert folder.exists()
        assert (folder / "manifest.json").is_file()
        assert (folder / "events.json").is_file()
        assert (folder / "timeline.json").is_file()
        assert (folder / "system_info.json").is_file()
        assert (folder / "README.txt").is_file()

        # Check manifest
        manifest = mgr.get_manifest(incident_id)
        assert manifest["incident_id"] == incident_id
        assert "events.json" in manifest["files"]
        assert "manifest.json" not in manifest["files"]  # Manifest does not self-reference

        # Verify integrity
        verification = mgr.verify(incident_id)
        assert verification["valid"] is True
        assert verification["files"]["events.json"]["valid"] is True

        # Test tampering detection
        events_file = folder / "events.json"
        original_content = events_file.read_text(encoding="utf-8")
        events_file.write_text(original_content + "\n// tampered", encoding="utf-8")
        tampered_verification = mgr.verify(incident_id)
        assert tampered_verification["valid"] is False
        assert tampered_verification["files"]["events.json"]["valid"] is False

        # Restore original content
        events_file.write_text(original_content, encoding="utf-8")
        restored_verification = mgr.verify(incident_id)
        assert restored_verification["valid"] is True

        # Test zip creation
        zip_result = mgr.zip(incident_id)
        zip_path = Path(zip_result)
        assert zip_path.exists()
        assert zip_path.stat().st_size > 0

    finally:
        # Cleanup generated test evidence
        if folder_path and folder_path.exists():
            shutil.rmtree(folder_path, ignore_errors=True)
        if zip_path and zip_path.exists():
            zip_path.unlink(missing_ok=True)
