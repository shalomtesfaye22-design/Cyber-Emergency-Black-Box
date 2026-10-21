"""Event ingestion and retrieval service."""

from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.collectors.normaliser import normalise
from backend.database import crud
from backend.database.models import EventModel
from backend.models.event import NormalisedEvent, event_dict


class EventService:
    """Encapsulates business logic for security event ingestion, cryptographic chaining, and querying."""

    @staticmethod
    async def ingest(
        session: AsyncSession,
        raw_event: dict[str, Any],
        correlation_engine: Any = None,
    ) -> EventModel:
        """Ingest, normalize, cryptographically chain, and persist a raw event.
        Optionally triggers correlation engine analysis.
        """
        # Cryptographic hash chaining: link with previous event's hash
        previous_hash = await crud.get_latest_event_hash(session)
        normalised: NormalisedEvent = normalise(raw_event, previous_hash=previous_hash)

        # Persist event
        saved = await crud.insert_event(session, normalised)

        # Trigger correlation analysis if engine is provided
        if correlation_engine is not None:
            await correlation_engine.run_once(session)

        return saved

    @staticmethod
    async def get_events(
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        event_type: str | None = None,
        severity: str | None = None,
        since: datetime | None = None,
        simulated_only: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve paginated and filtered events."""
        rows = await crud.get_events(
            session=session,
            limit=limit,
            offset=offset,
            event_type=event_type,
            severity=severity,
            since=since,
            simulated_only=simulated_only,
        )
        return [event_dict(x) for x in rows]

    @staticmethod
    async def get_event_by_id(
        session: AsyncSession, event_id: str
    ) -> dict[str, Any] | None:
        """Retrieve a single event by ID."""
        row = await crud.get_event_by_id(session, event_id)
        return event_dict(row) if row else None

    @staticmethod
    async def get_event_stats(session: AsyncSession) -> dict[str, int]:
        """Aggregate event counts by event type."""
        return await crud.get_event_counts_by_type(session)
