"""Unit tests for services: EventService, IncidentService, and RollingBufferService."""

from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.models.incident import IncidentStatusUpdate
from backend.services.event_service import EventService
from backend.services.incident_service import IncidentService
from backend.services.rolling_buffer import RollingBufferService


@pytest.mark.asyncio
async def test_event_service_cryptographic_hash_chaining(db_session: AsyncSession):
    """Verify that EventService automatically chains previous_hash to the preceding event."""
    # 1. Ingest first event -> previous_hash should be None
    ev1 = await EventService.ingest(
        db_session,
        {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "login_failure",
            "source": "test",
            "user_name": "bob",
        },
    )
    assert ev1.raw_hash is not None
    assert ev1.previous_hash is None

    # 2. Ingest second event -> previous_hash must match ev1.raw_hash
    ev2 = await EventService.ingest(
        db_session,
        {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "login_success",
            "source": "test",
            "user_name": "bob",
        },
    )
    assert ev2.raw_hash is not None
    assert ev2.previous_hash == ev1.raw_hash

    # 3. Ingest third event -> previous_hash must match ev2.raw_hash
    ev3 = await EventService.ingest(
        db_session,
        {
            "timestamp": datetime.now(timezone.utc),
            "event_type": "process_start",
            "source": "test",
            "process_name": "powershell.exe",
        },
    )
    assert ev3.previous_hash == ev2.raw_hash


@pytest.mark.asyncio
async def test_event_stats_uses_grouped_database_counts(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    for index, event_type in enumerate(("login_failure", "login_failure", "process_start")):
        await crud.insert_event(
            db_session,
            {
                "event_id": f"stats-{index}",
                "timestamp": now,
                "event_type": event_type,
                "source": "test",
            },
        )

    assert await EventService.get_event_stats(db_session) == {
        "login_failure": 2,
        "process_start": 1,
    }


@pytest.mark.asyncio
async def test_incident_service_valid_statuses(db_session: AsyncSession):
    """Test incident service status lifecycle transitions (FR-023)."""
    now = datetime.now(timezone.utc)
    incident_data = {
        "incident_id": "INC-TEST-002",
        "detection_time": now,
        "rule_id": "R-02",
        "rule_name": "Suspicious Process Sequence",
        "severity": "CRITICAL",
        "status": "OPEN",
        "summary": "Process test summary",
        "event_count": 0,
    }
    await crud.insert_incident(db_session, incident_data)

    # Test valid transitions
    for status in ["INVESTIGATING", "RESOLVED", "FALSE_POSITIVE", "OPEN"]:
        updated = await IncidentService.update_status(db_session, "INC-TEST-002", status)
        assert updated is not None
        assert updated["status"] == status

    # Verify Pydantic validation rejects unknown statuses
    with pytest.raises(ValueError):
        IncidentStatusUpdate(status="INVALID_STATUS")


@pytest.mark.asyncio
async def test_rolling_buffer_service_cleanup(db_session: AsyncSession):
    """Test RollingBufferService cleanup execution."""
    purged = await RollingBufferService.cleanup(db_session, retention_minutes=30)
    assert purged >= 0
