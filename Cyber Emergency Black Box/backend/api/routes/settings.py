"""Application configuration and settings endpoints."""

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.schemas.common import ok
from backend.database import crud
from backend.database.engine import get_db
from backend.api.routes.auth import require_authenticated
from backend.config import settings

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_authenticated)])

PERMITTED_KEYS: set[str] = {
    "retention_minutes",
    "correlation_interval_seconds",
    "evidence_context_minutes",
    "enabled_collectors",
}
VALID_COLLECTORS: set[str] = {"login", "process", "file", "network", "system_info", "usb"}


@router.get("")
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    """Retrieve runtime settings."""
    raw = await crud.get_settings(db)
    result: dict[str, Any] = {}
    for key, value in raw.items():
        if key in {"master_password_hash", "master_password_salt"}:
            continue
        try:
            result[key] = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            result[key] = value
    result["monitored_paths"] = settings.monitored_paths
    return ok(result)


@router.put("")
async def update_settings(body: dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Update runtime settings with validation."""
    if not body or set(body.keys()) - PERMITTED_KEYS:
        raise HTTPException(status_code=422, detail="unsupported setting key")

    for key in ("retention_minutes", "correlation_interval_seconds", "evidence_context_minutes"):
        if key in body and (not isinstance(body[key], int) or body[key] <= 0):
            raise HTTPException(status_code=422, detail=f"{key} must be a positive integer")

    if "enabled_collectors" in body:
        collectors = body["enabled_collectors"]
        if not isinstance(collectors, list) or not set(collectors).issubset(VALID_COLLECTORS):
            raise HTTPException(status_code=422, detail="invalid enabled collectors")

    updated = await crud.update_settings(db, body)
    return ok(updated)
