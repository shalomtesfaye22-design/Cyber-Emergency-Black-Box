"""Evidence API schemas."""

from typing import Any
from pydantic import BaseModel, Field


class EvidenceFileManifest(BaseModel):
    sha256: str
    size_bytes: int


class EvidenceManifest(BaseModel):
    incident_id: str
    created_at: str
    created_by: str
    files: dict[str, EvidenceFileManifest]


class FileVerificationResult(BaseModel):
    valid: bool
    expected: str
    actual: str | None


class EvidenceVerificationResponse(BaseModel):
    results: dict[str, FileVerificationResult]
