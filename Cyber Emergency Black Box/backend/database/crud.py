"""Database operations for the local Cyber Emergency Black Box database."""

import json
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import (
    EventModel,
    IncidentEventModel,
    IncidentModel,
    SettingsModel,
    SystemSnapshotModel,
)

DEFAULT_SETTINGS: dict[str, str] = {
    "retention_minutes": "30",
    "correlation_interval_seconds": "10",
    "evidence_context_minutes": "5",
    "enabled_collectors": '["login","process","file","network","system_info"]',
}


async def seed_default_settings(session: AsyncSession) -> int:
    """Seed default settings rows if not already present."""
    inserted = 0
    for key, value in DEFAULT_SETTINGS.items():
        if await session.get(SettingsModel, key) is None:
            session.add(SettingsModel(key=key, value=value))
            inserted += 1
    await session.commit()
    return inserted


async def get_latest_event_hash(session: AsyncSession) -> str | None:
    """Retrieve the raw_hash of the most recently created event for cryptographic hash chaining."""
    stmt = (
        select(EventModel.raw_hash)
        .order_by(EventModel.timestamp.desc())
        .limit(1)
    )
    return await session.scalar(stmt)


async def insert_event(session: AsyncSession, event: Any) -> EventModel:
    """Insert a single normalized event into the database."""
    data = event.model_dump() if hasattr(event, "model_dump") else dict(event)
    data["metadata_json"] = json.dumps(data.pop("metadata", {}), default=str)
    obj = EventModel(**data)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def insert_events_bulk(session: AsyncSession, events: list[Any]) -> list[EventModel]:
    """Insert multiple normalized events in a single batch transaction."""
    models: list[EventModel] = []
    for item in events:
        data = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        data["metadata_json"] = json.dumps(data.pop("metadata", {}), default=str)
        model = EventModel(**data)
        session.add(model)
        models.append(model)
    await session.commit()
    return models


async def get_events(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    event_type: str | None = None,
    severity: str | None = None,
    since: datetime | None = None,
    simulated_only: bool | None = None,
) -> list[EventModel]:
    """Query events with optional filtering and pagination."""
    q = select(EventModel).order_by(EventModel.timestamp.desc()).limit(limit).offset(offset)
    if event_type:
        q = q.where(EventModel.event_type == event_type)
    if severity:
        q = q.where(EventModel.severity == severity.upper())
    if since:
        q = q.where(EventModel.timestamp >= since)
    if simulated_only is not None:
        q = q.where(EventModel.is_simulated == simulated_only)
    return list((await session.scalars(q)).all())


async def get_events_since(session: AsyncSession, since: datetime) -> list[EventModel]:
    """Query all events ordered chronologically starting from a cutoff timestamp."""
    q = select(EventModel).where(EventModel.timestamp >= since).order_by(EventModel.timestamp.asc())
    return list((await session.scalars(q)).all())


async def event_count(session: AsyncSession) -> int:
    """Return total number of events stored."""
    return await session.scalar(select(func.count()).select_from(EventModel)) or 0


async def get_event_counts_by_type(session: AsyncSession) -> dict[str, int]:
    """Return event totals grouped by type using a database-side aggregate."""
    rows = await session.execute(
        select(EventModel.event_type, func.count(EventModel.event_id))
        .group_by(EventModel.event_type)
    )
    return {event_type: int(count) for event_type, count in rows.all()}


async def get_event_by_id(session: AsyncSession, event_id: str) -> EventModel | None:
    """Retrieve an event by its unique UUID."""
    return await session.get(EventModel, event_id)


async def insert_incident(session: AsyncSession, data: dict[str, Any]) -> IncidentModel:
    """Create a new incident record."""
    payload = dict(data)
    if isinstance(payload.get("interpretation"), (dict, list)):
        payload["interpretation"] = json.dumps(payload["interpretation"], default=str)
    obj = IncidentModel(**payload)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_incidents(
    session: AsyncSession,
    status: str | None = None,
    severity: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[IncidentModel]:
    """Query incidents ordered by detection time with optional filtering."""
    q = select(IncidentModel).order_by(IncidentModel.detection_time.desc()).limit(limit).offset(offset)
    if status:
        q = q.where(IncidentModel.status == status.upper())
    if severity:
        q = q.where(IncidentModel.severity == severity.upper())
    return list((await session.scalars(q)).all())


async def get_incident_by_id(session: AsyncSession, incident_id: str) -> IncidentModel | None:
    """Retrieve an incident by ID."""
    return await session.get(IncidentModel, incident_id)


async def update_incident_status(
    session: AsyncSession, incident_id: str, status: str
) -> IncidentModel | None:
    """Update status of an incident."""
    item = await get_incident_by_id(session, incident_id)
    if item:
        item.status = status.upper()
        await session.commit()
        await session.refresh(item)
    return item


async def link_events_to_incident(
    session: AsyncSession, incident_id: str, event_ids: list[str]
) -> None:
    """Link event UUIDs to an incident and set preserved=True on each linked event."""
    unique_ids = set(event_ids)
    for event_id in unique_ids:
        session.add(IncidentEventModel(incident_id=incident_id, event_id=event_id))

    # Mark all linked events as preserved so retention purges never delete them
    q = select(EventModel).where(EventModel.event_id.in_(unique_ids))
    events = (await session.scalars(q)).all()
    for ev in events:
        ev.preserved = True
    await session.commit()


async def get_events_for_incident(
    session: AsyncSession, incident_id: str
) -> list[EventModel]:
    """Retrieve all preserved events linked to a specific incident in chronological order."""
    q = (
        select(EventModel)
        .join(IncidentEventModel, IncidentEventModel.event_id == EventModel.event_id)
        .where(IncidentEventModel.incident_id == incident_id)
        .order_by(EventModel.timestamp.asc())
    )
    return list((await session.scalars(q)).all())


async def get_settings(session: AsyncSession) -> dict[str, str]:
    """Retrieve all settings key-value pairs."""
    return {x.key: x.value for x in (await session.scalars(select(SettingsModel))).all()}


async def update_settings(session: AsyncSession, values: dict[str, Any]) -> dict[str, str]:
    """Update settings entries."""
    for key, value in values.items():
        row = await session.get(SettingsModel, key)
        if row:
            row.value = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
        else:
            session.add(
                SettingsModel(
                    key=key,
                    value=json.dumps(value) if isinstance(value, (list, dict)) else str(value),
                )
            )
    await session.commit()
    return await get_settings(session)


async def insert_system_snapshot(session: AsyncSession, data: dict[str, Any]) -> SystemSnapshotModel:
    """Save a system information snapshot."""
    payload = dict(data)
    if not payload.get("snapshot_id"):
        import uuid
        payload["snapshot_id"] = str(uuid.uuid4())
    payload["metadata_json"] = json.dumps(payload.pop("metadata", {}), default=str)
    obj = SystemSnapshotModel(**payload)
    session.add(obj)
    await session.commit()
    return obj


async def get_latest_system_snapshot(session: AsyncSession) -> SystemSnapshotModel | None:
    """Retrieve the most recently recorded host snapshot."""
    stmt = (
        select(SystemSnapshotModel)
        .order_by(SystemSnapshotModel.captured_at.desc())
        .limit(1)
    )
    return await session.scalar(stmt)


async def delete_unpreserved_events_older_than(
    session: AsyncSession, cutoff: datetime
) -> int:
    """Delete unpreserved events older than the given cutoff timestamp (FR-010, FR-011)."""
    stmt = delete(EventModel).where(
        EventModel.timestamp < cutoff, EventModel.preserved.is_(False)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount or 0
