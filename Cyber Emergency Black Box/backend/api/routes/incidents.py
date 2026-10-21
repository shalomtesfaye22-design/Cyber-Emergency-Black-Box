"""Incident endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.schemas.common import ok
from backend.database.engine import get_db
from backend.database import crud
from backend.evidence.manager import EvidenceManager
from backend.models.incident import IncidentStatusUpdate
from backend.reports.html_report import generate_html_report
from backend.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("")
async def list_incidents(
    status: str | None = None,
    severity: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Query incidents ordered by detection time."""
    rows = await IncidentService.get_incidents(
        session=db,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return ok(rows, {"limit": limit, "offset": offset, "count": len(rows)})


@router.get("/{incident_id}")
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full incident details including all linked events."""
    data = await IncidentService.get_incident_detail(db, incident_id)
    if not data:
        raise HTTPException(status_code=404, detail="incident not found")
    return ok(data)


@router.patch("/{incident_id}")
async def update_incident(
    incident_id: str,
    body: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update incident status (OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE)."""
    updated = await IncidentService.update_status(db, incident_id, body.status)
    if not updated:
        raise HTTPException(status_code=404, detail="incident not found")
    return ok(updated)


@router.get("/{incident_id}/timeline")
async def get_timeline(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve chronological event timeline for an incident."""
    timeline = await IncidentService.get_timeline(db, incident_id)
    return ok(timeline)


@router.get("/{incident_id}/report", response_class=HTMLResponse)
async def get_incident_report(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Render a printable HTML forensic report for the incident."""
    item = await crud.get_incident_by_id(db, incident_id)
    if not item:
        raise HTTPException(status_code=404, detail="incident not found")
    events = await crud.get_events_for_incident(db, incident_id)
    try:
        manifest = EvidenceManager().get_manifest(incident_id)
    except Exception:
        manifest = {"files": {}}
    snapshot = await crud.get_latest_system_snapshot(db)
    system = {} if snapshot is None else {
        "hostname": snapshot.hostname,
        "os_name": snapshot.os_name,
        "os_version": snapshot.os_version,
        "captured_at": snapshot.captured_at.isoformat() if snapshot.captured_at else None,
        "uptime_seconds": snapshot.uptime_seconds,
    }
    return generate_html_report(item, events, item.interpretation or "", manifest, system=system)
