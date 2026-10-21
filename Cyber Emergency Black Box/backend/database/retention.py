"""Rolling event retention policy enforcement."""

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.crud import delete_unpreserved_events_older_than


async def purge_old_events(session: AsyncSession, retention_minutes: int) -> int:
    """Purge unpreserved events older than retention_minutes (FR-010, FR-011).
    Events marked with preserved=True are permanently kept.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=retention_minutes)
    return await delete_unpreserved_events_older_than(session, cutoff)
