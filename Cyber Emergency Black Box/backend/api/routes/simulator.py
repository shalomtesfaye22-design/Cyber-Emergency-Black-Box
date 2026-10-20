"""Event simulator endpoints."""

import asyncio
from fastapi import APIRouter, Request
from backend.api.schemas.common import ok
from simulator.scenarios.account_compromise import AccountCompromiseScenario

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.post("/run")
async def run_scenario(request: Request):
    """Trigger the simulated account compromise sequence."""
    ingest_fn = getattr(request.app.state, "ingest_fn", None)
    if not ingest_fn:
        # Fallback to importing ingest from main if needed
        from backend.services.event_service import EventService
        from backend.database.engine import get_session_factory

        async def _fallback_ingest(raw: dict):
            correlation_engine = getattr(request.app.state, "correlation_engine", None)
            async with get_session_factory()() as session:
                return await EventService.ingest(session, raw, correlation_engine)

        ingest_fn = _fallback_ingest

    asyncio.create_task(AccountCompromiseScenario().run(ingest_fn))
    return ok({"started": True, "scenario": "account_compromise"})


@router.get("/scenarios")
async def list_scenarios():
    """List available synthetic simulation scenarios."""
    return ok(["account_compromise"])
