import json
from datetime import datetime, timezone
from sqlalchemy import select
from backend.database.models import IncidentEventModel, IncidentModel, EventModel
from backend.database.crud import insert_incident, link_events_to_incident, get_events_for_incident
from backend.models.event import event_dict, NormalisedEvent
from backend.interpreter.interpreter import Interpreter
from backend.evidence.manager import EvidenceManager
from backend.correlation.rules.rules import AccountCompromiseRule,SuspiciousProcessRule,FileActivityRule
class CorrelationEngine:
    def __init__(self): self.rules=[AccountCompromiseRule(),SuspiciousProcessRule(),FileActivityRule()]
    async def run_once(self,session):
        rows=list((await session.scalars(select(EventModel).order_by(EventModel.timestamp))).all()); events=[NormalisedEvent(**event_dict(x)) for x in rows]; created=[]
        for rule in self.rules:
            result=rule.evaluate(events)
            if not result: continue
            linked=select(IncidentEventModel.incident_id).where(IncidentEventModel.event_id.in_(result.event_ids))
            previous=set((await session.scalars(linked)).all())
            if previous: continue
            incident_id=f"INC-{datetime.now(timezone.utc):%Y%m%d}-{len(created)+1:04d}"
            incident=await insert_incident(session,{"incident_id":incident_id,"detection_time":datetime.now(timezone.utc),"rule_id":result.rule_id,"rule_name":result.name,"severity":result.severity,"status":"OPEN","summary":result.explanation,"event_count":len(result.event_ids)})
            await link_events_to_incident(session,incident_id,result.event_ids); linked_events=await get_events_for_incident(session,incident_id); interpretation=Interpreter().interpret(incident,linked_events)
            incident.interpretation=interpretation.model_dump_json(); await session.commit(); await EvidenceManager().preserve(session,incident_id,interpretation.model_dump()); created.append(incident)
        return created
