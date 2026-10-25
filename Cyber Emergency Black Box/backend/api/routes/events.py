"""Event endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.schemas.common import ok
from backend.database.engine import get_db
from backend.models.event import EventCreate, event_dict
from backend.services.event_service import EventService
from backend.api.routes.auth import require_authenticated

router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(require_authenticated)])


@router.post("")
async def create_event(
    body: EventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single security event."""
    correlation_engine = getattr(request.app.state, "correlation_engine", None)
    saved = await EventService.ingest(
        session=db,
        raw_event=body.model_dump(),
        correlation_engine=correlation_engine,
    )
    return ok(event_dict(saved))


@router.get("")
async def list_events(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: str | None = None,
    severity: str | None = None,
    simulated_only: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List events with optional filtering and pagination."""
    rows = await EventService.get_events(
        session=db,
        limit=limit,
        offset=offset,
        event_type=event_type,
        severity=severity,
        simulated_only=simulated_only,
    )
    return ok(rows, {"limit": limit, "offset": offset, "count": len(rows)})


@router.get("/stats")
async def event_statistics(db: AsyncSession = Depends(get_db)):
    """Retrieve event counts grouped by event type."""
    stats = await EventService.get_event_stats(db)
    return ok(stats)


@router.get("/{event_id}")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a single event by ID."""
    row = await EventService.get_event_by_id(db, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="event not found")
    return ok(row)
