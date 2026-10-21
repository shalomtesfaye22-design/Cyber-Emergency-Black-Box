"""Bounded-window, explainable correlation orchestration."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from backend.correlation.rules.account_compromise import AccountCompromiseRule
from backend.correlation.rules.file_activity import FileActivityRule
from backend.correlation.rules.suspicious_process import SuspiciousProcessRule
from backend.database import crud
from backend.database.models import EventModel, IncidentEventModel, IncidentModel
from backend.evidence.manager import EvidenceManager
from backend.interpreter.interpreter import Interpreter
from backend.models.event import NormalisedEvent, event_dict


class CorrelationEngine:
    """Evaluate registered rules without loading historical event data."""
    def __init__(self, rules=None):
        self.rules = rules or [AccountCompromiseRule(), SuspiciousProcessRule(), FileActivityRule()]

    async def _recent_events(self, session):
        now = datetime.now(timezone.utc)
        maximum_window = max(rule.time_window_seconds for rule in self.rules)
        cutoff = now - timedelta(seconds=maximum_window + 60)
        upper_bound = now + timedelta(seconds=maximum_window)
        query = (
            select(EventModel)
            .where(EventModel.timestamp >= cutoff, EventModel.timestamp <= upper_bound)
            .order_by(EventModel.timestamp)
        )
        rows = list((await session.scalars(query)).all())
        return [NormalisedEvent(**event_dict(row)) for row in rows]

    async def _duplicate(self, session, event_ids):
        target = set(event_ids)
        query = select(IncidentEventModel.incident_id).where(IncidentEventModel.event_id.in_(target))
        for incident_id in set((await session.scalars(query)).all()):
            existing = await crud.get_events_for_incident(session, incident_id)
            if {event.event_id for event in existing} == target:
                return True
        return False

    async def _next_incident_id(self, session):
        prefix = f"INC-{datetime.now(timezone.utc):%Y%m%d}-"
        count = await session.scalar(select(func.count()).select_from(IncidentModel).where(IncidentModel.incident_id.like(f"{prefix}%")))
        return f"{prefix}{(count or 0) + 1:04d}"

    async def run_once(self, session):
        events, created = await self._recent_events(session), []
        for rule in self.rules:
            result = rule.evaluate(events)
            if result is None or await self._duplicate(session, result.event_ids):
                continue
            incident_id = await self._next_incident_id(session)
            incident = await crud.insert_incident(session, {"incident_id": incident_id, "detection_time": datetime.now(timezone.utc), "rule_id": result.rule_id, "rule_name": result.name, "severity": result.severity, "status": "OPEN", "summary": result.explanation, "event_count": len(set(result.event_ids))})
            await crud.link_events_to_incident(session, incident_id, result.event_ids)
            linked_events = await crud.get_events_for_incident(session, incident_id)
            interpretation = Interpreter().interpret(incident, linked_events, result)
            incident.interpretation = interpretation.model_dump_json()
            await session.commit()
            await EvidenceManager().preserve(session, incident_id, interpretation.model_dump(mode="json"))
            created.append(incident)
        return created
