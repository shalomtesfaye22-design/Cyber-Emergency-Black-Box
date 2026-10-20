"""Unit tests for database CRUD, models, and retention logic."""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud
from backend.database.models import EventModel
from backend.database.retention import purge_old_events


@pytest.mark.asyncio
async def test_seed_default_settings(db_session: AsyncSession):
    """Test default settings seeding and idempotency."""
    settings = await crud.get_settings(db_session)
    assert "retention_minutes" in settings
    assert "correlation_interval_seconds" in settings

    # Calling again should insert 0 rows (idempotent)
    second_run = await crud.seed_default_settings(db_session)
    assert second_run == 0



@pytest.mark.asyncio
async def test_insert_and_get_event(db_session: AsyncSession):
    """Test inserting and retrieving a single event."""
    event_data = {
        "event_id": "test-uuid-001",
        "timestamp": datetime.now(timezone.utc),
        "event_type": "login_failure",
        "source": "test",
        "user_name": "alice",
        "raw_hash": "hash001",
        "previous_hash": None,
        "is_simulated": True,
        "preserved": False,
        "metadata": {"attempt": 1},
    }
    saved = await crud.insert_event(db_session, event_data)
    assert saved.event_id == "test-uuid-001"
    assert saved.user_name == "alice"

    retrieved = await crud.get_event_by_id(db_session, "test-uuid-001")
    assert retrieved is not None
    assert retrieved.event_type == "login_failure"


@pytest.mark.asyncio
async def test_insert_events_bulk(db_session: AsyncSession):
    """Test bulk event insertion."""
    now = datetime.now(timezone.utc)
    events = [
        {
            "event_id": f"bulk-uuid-{i}",
            "timestamp": now + timedelta(seconds=i),
            "event_type": "process_start",
            "source": "test",
            "process_name": f"proc_{i}.exe",
            "raw_hash": f"hash_{i}",
            "previous_hash": f"hash_{i-1}" if i > 0 else None,
            "is_simulated": False,
            "preserved": False,
        }
        for i in range(5)
    ]
    inserted = await crud.insert_events_bulk(db_session, events)
    assert len(inserted) == 5

    count = await crud.event_count(db_session)
    assert count == 5


@pytest.mark.asyncio
async def test_get_events_since(db_session: AsyncSession):
    """Test bounded time-window queries for correlation efficiency."""
    now = datetime.now(timezone.utc)
    old_event = {
        "event_id": "old-001",
        "timestamp": now - timedelta(minutes=15),
        "event_type": "login_failure",
        "source": "test",
    }
    new_event = {
        "event_id": "new-001",
        "timestamp": now - timedelta(minutes=2),
        "event_type": "login_success",
        "source": "test",
    }
    await crud.insert_event(db_session, old_event)
    await crud.insert_event(db_session, new_event)

    # Query events since 5 minutes ago
    cutoff = now - timedelta(minutes=5)
    recent = await crud.get_events_since(db_session, cutoff)
    assert len(recent) == 1
    assert recent[0].event_id == "new-001"


@pytest.mark.asyncio
async def test_retention_purge_spares_preserved_events(db_session: AsyncSession):
    """Test that retention purge deletes expired events but strictly keeps preserved events (FR-010, FR-011)."""
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(minutes=45)

    # 1. Old unpreserved event -> should be purged
    ev1 = {
        "event_id": "purge-target",
        "timestamp": expired_time,
        "event_type": "file_modified",
        "source": "test",
        "preserved": False,
    }
    # 2. Old preserved event (e.g. linked to incident) -> must NEVER be purged
    ev2 = {
        "event_id": "preserved-forensic",
        "timestamp": expired_time,
        "event_type": "file_modified",
        "source": "test",
        "preserved": True,
    }
    # 3. Recent unpreserved event -> within retention window
    ev3 = {
        "event_id": "recent-event",
        "timestamp": now - timedelta(minutes=5),
        "event_type": "file_created",
        "source": "test",
        "preserved": False,
    }

    await crud.insert_event(db_session, ev1)
    await crud.insert_event(db_session, ev2)
    await crud.insert_event(db_session, ev3)

    # Purge events older than 30 minutes
    purged_count = await purge_old_events(db_session, retention_minutes=30)
    assert purged_count == 1

    # Verify purge results
    assert await crud.get_event_by_id(db_session, "purge-target") is None
    assert await crud.get_event_by_id(db_session, "preserved-forensic") is not None
    assert await crud.get_event_by_id(db_session, "recent-event") is not None


@pytest.mark.asyncio
async def test_incident_crud_and_event_linking(db_session: AsyncSession):
    """Test incident creation, event linking, and status transitions."""
    now = datetime.now(timezone.utc)
    ev = await crud.insert_event(
        db_session,
        {
            "event_id": "inc-event-01",
            "timestamp": now,
            "event_type": "login_failure",
            "source": "test",
            "preserved": False,
        },
    )

    incident_data = {
        "incident_id": "INC-20261020-0001",
        "detection_time": now,
        "rule_id": "R-01",
        "rule_name": "Possible Account Compromise",
        "severity": "HIGH",
        "status": "OPEN",
        "summary": "Suspicious login pattern detected",
        "event_count": 1,
    }
    incident = await crud.insert_incident(db_session, incident_data)
    assert incident.incident_id == "INC-20261020-0001"

    # Link event to incident
    await crud.link_events_to_incident(db_session, incident.incident_id, ["inc-event-01"])

    # Linked event must now have preserved=True
    reloaded_ev = await crud.get_event_by_id(db_session, "inc-event-01")
    assert reloaded_ev.preserved is True

    # Update incident status to INVESTIGATING and then RESOLVED
    updated = await crud.update_incident_status(db_session, incident.incident_id, "INVESTIGATING")
    assert updated.status == "INVESTIGATING"

    updated = await crud.update_incident_status(db_session, incident.incident_id, "RESOLVED")
    assert updated.status == "RESOLVED"
