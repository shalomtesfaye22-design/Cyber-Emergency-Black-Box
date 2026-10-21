"""Evidence preservation and verification endpoints."""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.api.schemas.common import ok
from backend.evidence.manager import EvidenceManager

router = APIRouter(prefix="/incidents", tags=["evidence"])


@router.get("/{incident_id}/evidence")
async def get_evidence_manifest(incident_id: str):
    """Retrieve manifest containing SHA-256 hashes for all preserved files."""
    try:
        manifest = EvidenceManager().get_manifest(incident_id)
        return ok(manifest)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="evidence not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{incident_id}/evidence/verify")
async def verify_evidence(incident_id: str):
    """Recompute hashes and verify cryptographic integrity of preserved evidence."""
    try:
        results = EvidenceManager().verify(incident_id)
        return ok(results)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="evidence not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{incident_id}/evidence/download")
async def download_evidence(incident_id: str):
    """Download the complete evidence package as a ZIP archive."""
    try:
        zip_path = EvidenceManager().zip(incident_id)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{incident_id}_evidence.zip",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="evidence not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
