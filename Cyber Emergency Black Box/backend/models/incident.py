"""Domain models for security incidents."""

import json
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

VALID_STATUSES: set[str] = {"OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"}
VALID_SEVERITIES: set[str] = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}


class IncidentStatusUpdate(BaseModel):
    """Schema for updating the status of an existing incident."""

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )
        return v


class InterpretationResult(BaseModel):
    """Structured log interpretation output (FR-036)."""

    confirmed_facts: list[str] = Field(default_factory=list)
    detection_result: str = ""
    interpretation: str = ""
    recommendations: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Automated forensic analysis requires human verification. "
        "This assessment indicates a suspicious pattern and is not definitive legal or technical proof of breach."
    )


class IncidentCreate(BaseModel):
    """Internal model for incident creation."""

    incident_id: str
    detection_time: datetime
    rule_id: str
    rule_name: str
    severity: str = "MEDIUM"
    status: str = "OPEN"
    summary: str
    interpretation: str | None = None
    evidence_path: str | None = None
    event_count: int = 0

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{v}'")
        return v


def incident_dict(item: Any) -> dict[str, Any]:
    """Convert an IncidentModel SQLAlchemy instance into an API-friendly dictionary."""
    interpretation_data = None
    if item.interpretation:
        try:
            interpretation_data = json.loads(item.interpretation)
        except Exception:
            interpretation_data = item.interpretation

    return {
        "incident_id": item.incident_id,
        "detection_time": item.detection_time.isoformat()
        if isinstance(item.detection_time, datetime)
        else item.detection_time,
        "rule_id": item.rule_id,
        "rule_name": item.rule_name,
        "severity": item.severity,
        "status": item.status,
        "summary": item.summary,
        "interpretation": interpretation_data,
        "evidence_path": item.evidence_path,
        "event_count": item.event_count,
    }
