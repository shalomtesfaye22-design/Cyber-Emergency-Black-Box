import hashlib, json, uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, field_validator
EVENT_TYPES={"login_success","login_failure","process_start","process_stop","file_created","file_modified","file_deleted","network_connection","usb_connected","usb_disconnected","system_info","application_log"}
SEVERITIES={"INFO","LOW","MEDIUM","HIGH","CRITICAL"}
class EventCreate(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str; source: str
    user_name: str|None=None; process_name: str|None=None; action: str|None=None; target: str|None=None
    source_ip: str|None=None; destination_ip: str|None=None; destination_port: int|None=None; protocol: str|None=None
    metadata: dict[str,Any]=Field(default_factory=dict); severity: str="INFO"; is_simulated: bool=False
    @field_validator("timestamp")
    @classmethod
    def utc(cls,v):
        if v.tzinfo is None: raise ValueError("timestamp must include UTC timezone")
        return v.astimezone(timezone.utc)
    @field_validator("event_type")
    @classmethod
    def known_event(cls,v):
        if v not in EVENT_TYPES: raise ValueError("unsupported event type")
        return v
    @field_validator("severity")
    @classmethod
    def known_severity(cls,v):
        v=v.upper()
        if v not in SEVERITIES: raise ValueError("unsupported severity")
        return v
class NormalisedEvent(EventCreate):
    event_id: str=Field(default_factory=lambda:str(uuid.uuid4())); raw_hash: str|None=None; preserved: bool=False
class EventResponse(NormalisedEvent): pass

def event_dict(item):
    metadata=json.loads(item.metadata_json or "{}")
    return {"event_id":item.event_id,"timestamp":item.timestamp,"event_type":item.event_type,"source":item.source,"user_name":item.user_name,"process_name":item.process_name,"action":item.action,"target":item.target,"source_ip":item.source_ip,"destination_ip":item.destination_ip,"destination_port":item.destination_port,"protocol":item.protocol,"metadata":metadata,"severity":item.severity,"raw_hash":item.raw_hash,"is_simulated":item.is_simulated,"preserved":item.preserved}
