"""System information, health, and dashboard summary endpoints."""

import time
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.schemas.common import ok
from backend.collectors.system_info_collector import SystemInfoCollector
from backend.database import crud
from backend.database.engine import get_db

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """Service health check endpoint."""
    return ok({"status": "ok"})


@router.get("/system/info")
async def system_information(db: AsyncSession = Depends(get_db)):
    """Retrieve host system information."""
    snap = await crud.get_latest_system_snapshot(db)
    if not snap:
        snapshot_data = await SystemInfoCollector(None).snapshot()
        snap = await crud.insert_system_snapshot(db, snapshot_data)

    return ok(
        {
            "hostname": snap.hostname,
            "os_name": snap.os_name,
            "os_version": snap.os_version,
            "cpu_count": snap.cpu_count,
            "memory_total_gb": snap.memory_total_gb,
            "uptime_seconds": snap.uptime_seconds,
        }
    )


@router.get("/system/status")
async def system_status(request: Request):
    """Retrieve collector runtime status and process uptime."""
    started_time = getattr(request.app.state, "started_time", time.monotonic())
    collectors = getattr(request.app.state, "collectors", [])
    return ok(
        {
            "uptime_seconds": int(time.monotonic() - started_time),
            "collectors": [
                {"name": getattr(c, "name", "unknown"), "available": getattr(c, "available", True)}
                for c in collectors
            ],
        }
    )


@router.get("/dashboard/summary")
async def dashboard_summary(request: Request, db: AsyncSession = Depends(get_db)):
    """Summary metrics for the web dashboard."""
    started_time = getattr(request.app.state, "started_time", time.monotonic())
    event_count = await crud.event_count(db)
    incidents = await crud.get_incidents(db)

    severity_rank = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1}
    highest_severity = "INFO"
    if incidents:
        highest_severity = max(
            incidents, key=lambda x: severity_rank.get(x.severity, 0)
        ).severity

    return ok(
        {
            "event_count": event_count,
            "incident_count": len(incidents),
            "highest_severity": highest_severity,
            "uptime_seconds": int(time.monotonic() - started_time),
        }
    )
