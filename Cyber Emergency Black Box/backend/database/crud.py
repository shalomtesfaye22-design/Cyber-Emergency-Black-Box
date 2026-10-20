"""Small, explicit database operations used by services and routes."""
import json
from datetime import datetime, timezone
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import EventModel, IncidentModel, IncidentEventModel, SettingsModel, SystemSnapshotModel

DEFAULT_SETTINGS = {"retention_minutes": "30", "correlation_interval_seconds": "10", "evidence_context_minutes": "5", "enabled_collectors": '["login","process","file","network","system_info"]'}

async def seed_default_settings(session: AsyncSession):
    inserted = 0
    for key, value in DEFAULT_SETTINGS.items():
        if await session.get(SettingsModel, key) is None:
            session.add(SettingsModel(key=key, value=value)); inserted += 1
    await session.commit(); return inserted

async def insert_event(session, event):
    data = event.model_dump() if hasattr(event, "model_dump") else event
    data["metadata_json"] = json.dumps(data.pop("metadata", {}), default=str)
    obj = EventModel(**data); session.add(obj); await session.commit(); await session.refresh(obj); return obj

async def get_events(session, limit=100, offset=0, event_type=None, severity=None, since=None, simulated_only=None):
    q = select(EventModel).order_by(EventModel.timestamp.desc()).limit(limit).offset(offset)
    for column, value in ((EventModel.event_type,event_type),(EventModel.severity,severity)):
        if value: q=q.where(column==value)
    if since: q=q.where(EventModel.timestamp >= since)
    if simulated_only is not None: q=q.where(EventModel.is_simulated == simulated_only)
    return list((await session.scalars(q)).all())

async def event_count(session): return await session.scalar(select(func.count()).select_from(EventModel)) or 0
async def get_event_by_id(session, event_id): return await session.get(EventModel, event_id)
async def insert_incident(session, data):
    obj=IncidentModel(**data); session.add(obj); await session.commit(); await session.refresh(obj); return obj
async def get_incidents(session, status=None, severity=None, limit=100, offset=0):
    q=select(IncidentModel).order_by(IncidentModel.detection_time.desc()).limit(limit).offset(offset)
    if status: q=q.where(IncidentModel.status==status)
    if severity: q=q.where(IncidentModel.severity==severity)
    return list((await session.scalars(q)).all())
async def get_incident_by_id(session, incident_id): return await session.get(IncidentModel, incident_id)
async def update_incident_status(session, incident_id, status):
    item=await get_incident_by_id(session,incident_id)
    if item: item.status=status; await session.commit(); await session.refresh(item)
    return item
async def link_events_to_incident(session, incident_id, event_ids):
    for event_id in set(event_ids): session.add(IncidentEventModel(incident_id=incident_id,event_id=event_id))
    await session.execute(select(EventModel).where(EventModel.event_id.in_(set(event_ids))).with_for_update())
    for event_id in set(event_ids):
        event=await session.get(EventModel,event_id)
        if event: event.preserved=True
    await session.commit()
async def get_events_for_incident(session, incident_id):
    q=select(EventModel).join(IncidentEventModel, IncidentEventModel.event_id==EventModel.event_id).where(IncidentEventModel.incident_id==incident_id).order_by(EventModel.timestamp)
    return list((await session.scalars(q)).all())
async def get_settings(session): return {x.key:x.value for x in (await session.scalars(select(SettingsModel))).all()}
async def update_settings(session, values):
    for key,value in values.items():
        row=await session.get(SettingsModel,key)
        if row: row.value=json.dumps(value) if isinstance(value,(list,dict)) else str(value)
    await session.commit(); return await get_settings(session)
async def insert_system_snapshot(session, data):
    data["metadata_json"]=json.dumps(data.pop("metadata",{})); obj=SystemSnapshotModel(**data); session.add(obj); await session.commit(); return obj
async def get_latest_system_snapshot(session): return await session.scalar(select(SystemSnapshotModel).order_by(SystemSnapshotModel.captured_at.desc()).limit(1))

