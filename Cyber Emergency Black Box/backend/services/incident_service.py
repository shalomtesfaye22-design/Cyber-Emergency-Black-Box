"""Incident management service."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import crud
from backend.database.models import IncidentModel
from backend.models.event import event_dict
from backend.models.incident import incident_dict


class IncidentService:
    """Encapsulates incident lifecycle management and timeline retrieval."""

    @staticmethod
    async def get_incidents(
        session: AsyncSession,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List incidents with filtering."""
        rows = await crud.get_incidents(
            session=session,
            status=status,
            severity=severity,
            limit=limit,
            offset=offset,
        )
        return [incident_dict(x) for x in rows]

    @staticmethod
    async def get_incident_detail(
        session: AsyncSession, incident_id: str
    ) -> dict[str, Any] | None:
        """Retrieve full incident details including all linked events."""
        row = await crud.get_incident_by_id(session, incident_id)
        if not row:
            return None
        data = incident_dict(row)
        events = await crud.get_events_for_incident(session, incident_id)
        data["events"] = [event_dict(x) for x in events]
        return data

    @staticmethod
    async def update_status(
        session: AsyncSession, incident_id: str, status: str
    ) -> dict[str, Any] | None:
        """Transition an incident's status (OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE)."""
        row = await crud.update_incident_status(session, incident_id, status)
        return incident_dict(row) if row else None

    @staticmethod
    async def get_timeline(
        session: AsyncSession, incident_id: str
    ) -> list[dict[str, Any]]:
        """Retrieve chronological events for an incident timeline."""
        events = await crud.get_events_for_incident(session, incident_id)
        return [event_dict(x) for x in events]
