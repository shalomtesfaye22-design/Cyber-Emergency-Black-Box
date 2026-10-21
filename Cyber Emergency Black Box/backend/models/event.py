"""Domain models for security events."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, field_validator

EVENT_TYPES: set[str] = {
    "login_success",
    "login_failure",
    "process_start",
    "process_stop",
    "file_created",
    "file_modified",
    "file_deleted",
    "network_connection",
    "usb_connected",
    "usb_disconnected",
    "system_info",
    "application_log",
}

SEVERITIES: set[str] = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}


class EventCreate(BaseModel):
    """Schema for event ingestion."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    source: str
    user_name: str | None = None
    process_name: str | None = None
    action: str | None = None
    target: str | None = None
    source_ip: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = None
    protocol: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    severity: str = "INFO"
    is_simulated: bool = False

    @field_validator("timestamp")
    @classmethod
    def enforce_utc_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            raise ValueError(f"unsupported event type '{v}'")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        v = v.upper()
        if v not in SEVERITIES:
            raise ValueError(f"unsupported severity '{v}'")
        return v


class NormalisedEvent(EventCreate):
    """Canonical normalized event with UUID and cryptographic hashes."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_hash: str | None = None
    previous_hash: str | None = None
    preserved: bool = False


class EventResponse(NormalisedEvent):
    """Event representation returned via API."""

    pass


def event_dict(item: Any) -> dict[str, Any]:
    """Convert an EventModel SQLAlchemy instance into an API-friendly dictionary."""
    meta = {}
    if hasattr(item, "metadata_json") and item.metadata_json:
        try:
            meta = json.loads(item.metadata_json)
        except Exception:
            meta = {}
    elif hasattr(item, "metadata") and isinstance(item.metadata, dict):
        meta = item.metadata

    ts = item.timestamp
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts = ts.isoformat()

    return {
        "event_id": item.event_id,
        "timestamp": ts,
        "event_type": item.event_type,
        "source": item.source,
        "user_name": item.user_name,
        "process_name": item.process_name,
        "action": item.action,
        "target": item.target,
        "source_ip": item.source_ip,
        "destination_ip": item.destination_ip,
        "destination_port": item.destination_port,
        "protocol": item.protocol,
        "metadata": meta,
        "severity": item.severity,
        "raw_hash": getattr(item, "raw_hash", None),
        "previous_hash": getattr(item, "previous_hash", None),
        "is_simulated": getattr(item, "is_simulated", False),
        "preserved": getattr(item, "preserved", False),
    }
