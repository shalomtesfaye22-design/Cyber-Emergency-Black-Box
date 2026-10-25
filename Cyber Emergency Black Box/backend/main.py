"""Cyber Emergency Black Box — Main FastAPI Application Entrypoint."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import ensure_directories, settings
from backend.database.engine import get_session_factory, init_db
from backend.database import crud
from backend.services.event_service import EventService
from backend.services.rolling_buffer import RollingBufferService
from backend.collectors.registry import get_enabled_collectors
from backend.collectors.system_info_collector import SystemInfoCollector
from backend.correlation.engine import CorrelationEngine

# Routers
from backend.api.routes.events import router as events_router
from backend.api.routes.incidents import router as incidents_router
from backend.api.routes.evidence import router as evidence_router
from backend.api.routes.system import router as system_router
from backend.api.routes.settings import router as settings_router
from backend.api.routes.simulator import router as simulator_router
from backend.api.routes.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("blackbox")


async def _run_maintenance_loop(app: FastAPI) -> None:
    """Periodic background worker for collector execution, correlation analysis, and retention cleanup."""
    interval_seconds = settings.correlation_interval_seconds
    while True:
        try:
            # 1. Run periodic collectors
            for collector in getattr(app.state, "collectors", []):
                if hasattr(collector, "run_once"):
                    await collector.run_once()

            # 2. Run correlation analysis and rolling retention purge
            async with get_session_factory()() as session:
                runtime_settings = await crud.get_settings(session)
                try:
                    retention_minutes = int(runtime_settings.get("retention_minutes", settings.retention_minutes))
                    interval_seconds = max(
                        1,
                        int(runtime_settings.get("correlation_interval_seconds", settings.correlation_interval_seconds)),
                    )
                except (TypeError, ValueError):
                    logger.warning("Invalid persisted maintenance settings; using startup defaults")
                    retention_minutes = settings.retention_minutes
                    interval_seconds = settings.correlation_interval_seconds
                correlation_engine = getattr(app.state, "correlation_engine", None)
                if correlation_engine is not None:
                    await correlation_engine.run_once(session)

                await RollingBufferService.cleanup(session, retention_minutes)

        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Error during background maintenance cycle")

        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    ensure_directories()
    await init_db()

    app.state.started_time = time.monotonic()
    app.state.correlation_engine = CorrelationEngine()

    # Ingestion callback passed to collectors and simulator
    async def ingest(raw: dict[str, Any]):
        async with get_session_factory()() as session:
            return await EventService.ingest(
                session, raw, correlation_engine=app.state.correlation_engine
            )

    app.state.ingest_fn = ingest

    # Register enabled collectors
    paths = [p.strip() for p in settings.monitored_paths.split(",") if p.strip()]
    app.state.collectors = get_enabled_collectors(ingest, settings.enabled_collectors, paths)

    # Initial host system snapshot
    async with get_session_factory()() as session:
        snapshot_data = await SystemInfoCollector(ingest).snapshot()
        await crud.insert_system_snapshot(session, snapshot_data)

    # Start long-running collectors (e.g. file watcher observer thread)
    for c in app.state.collectors:
        if hasattr(c, "start"):
            c.start()

    # Start background maintenance loop
    app.state.maintenance_task = asyncio.create_task(_run_maintenance_loop(app))
    logger.info("Cyber Emergency Black Box started successfully")

    yield

    # Shutdown sequence
    if hasattr(app.state, "maintenance_task"):
        app.state.maintenance_task.cancel()
        try:
            await app.state.maintenance_task
        except asyncio.CancelledError:
            pass

    for c in getattr(app.state, "collectors", []):
        if hasattr(c, "stop"):
            c.stop()

    logger.info("Cyber Emergency Black Box stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to prevent leaking internals while logging tracebacks."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.exception("Unhandled server exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An internal error occurred."}},
    )


# Mount versioned API routes
API_PREFIX = "/api/v1"
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(incidents_router, prefix=API_PREFIX)
app.include_router(evidence_router, prefix=API_PREFIX)
app.include_router(settings_router, prefix=API_PREFIX)
app.include_router(simulator_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)

# Mount frontend static files if directory exists
if settings.frontend_dir.exists():
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port, reload=False)
