import json
from datetime import datetime
from pydantic import BaseModel, Field
STATUSES={"OPEN","INVESTIGATING","CLOSED"}
class IncidentStatusUpdate(BaseModel):
    status: str
    def model_post_init(self, __context):
        self.status=self.status.upper()
        if self.status not in STATUSES: raise ValueError("status must be OPEN, INVESTIGATING, or CLOSED")
class InterpretationResult(BaseModel):
    confirmed_facts: list[str]=Field(default_factory=list); detection_result: str=""; interpretation: str=""; recommendations: list[str]=Field(default_factory=list); disclaimer: str="Automated analysis requires human verification."
def incident_dict(item):
    return {"incident_id":item.incident_id,"detection_time":item.detection_time,"rule_id":item.rule_id,"rule_name":item.rule_name,"severity":item.severity,"status":item.status,"summary":item.summary,"interpretation":json.loads(item.interpretation) if item.interpretation else None,"evidence_path":item.evidence_path,"event_count":item.event_count}
