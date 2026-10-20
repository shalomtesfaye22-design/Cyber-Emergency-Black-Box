"""Rolling event retention and buffer management service."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.retention import purge_old_events

logger = logging.getLogger(__name__)


class RollingBufferService:
    """Manages the circular retention buffer of endpoint events."""

    @staticmethod
    async def cleanup(session: AsyncSession, retention_minutes: int) -> int:
        """Purge unpreserved events older than retention_minutes.
        Preserved events (linked to incidents) are guaranteed to never be purged (FR-010, FR-011).
        """
        try:
            purged = await purge_old_events(session, retention_minutes)
            if purged > 0:
                logger.info("Purged %d unpreserved events older than %d minutes", purged, retention_minutes)
            return purged
        except Exception:
            logger.exception("Rolling buffer purge cycle encountered an error")
            return 0
