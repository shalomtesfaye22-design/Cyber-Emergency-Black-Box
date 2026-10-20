from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from backend.database.models import EventModel
async def purge_old_events(session, retention_minutes: int):
    cutoff=datetime.now(timezone.utc)-timedelta(minutes=retention_minutes)
    result=await session.execute(delete(EventModel).where(EventModel.timestamp < cutoff, EventModel.preserved == False))
    await session.commit(); return result.rowcount or 0
