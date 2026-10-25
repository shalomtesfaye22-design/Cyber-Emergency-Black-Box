"""Single-operator master-password authentication for the local dashboard."""

import hashlib
import hmac
import re
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import ok
from backend.database import crud
from backend.database.engine import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])
SESSION_COOKIE = "cebb_session"
PBKDF2_ITERATIONS = 310_000


class PasswordBody(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class ChangePasswordBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=1, max_length=256)


def _password_error(password: str) -> str | None:
    if len(password) < 8:
        return "Password must contain at least 8 characters."
    if not re.search(r"[a-z]", password):
        return "Password must contain a lowercase letter."
    if not re.search(r"[A-Z]", password):
        return "Password must contain an uppercase letter."
    if not re.search(r"\d", password):
        return "Password must contain a digit."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Password must contain a symbol."
    return None


def _derive(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS).hex()


def _new_session(request: Request, response: Response) -> None:
    token = secrets.token_urlsafe(32)
    sessions = getattr(request.app.state, "auth_sessions", None)
    if not isinstance(sessions, dict):
        # Normalize state initialized by older versions or local test harnesses.
        sessions = {}
        request.app.state.auth_sessions = sessions
    sessions[token] = time.time() + 12 * 60 * 60
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, samesite="strict", secure=False,
        path="/", max_age=12 * 60 * 60,
    )


async def is_authenticated(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE)
    sessions = getattr(request.app.state, "auth_sessions", {})
    if not isinstance(sessions, dict):
        return False
    expires_at = sessions.get(token) if token else None
    if expires_at is not None and expires_at <= time.time():
        sessions.pop(token, None)
        return False
    return expires_at is not None


async def require_authenticated(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Protect application APIs until an operator has created a password and logged in."""
    values = await crud.get_settings(db)
    if not values.get("master_password_hash"):
        raise HTTPException(status_code=423, detail="Master password setup is required.")
    if not await is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required.")


@router.get("/status")
async def auth_status(request: Request, db: AsyncSession = Depends(get_db)):
    values = await crud.get_settings(db)
    return ok({
        "initialized": bool(values.get("master_password_hash") and values.get("master_password_salt")),
        "authenticated": await is_authenticated(request),
    })


@router.post("/setup")
async def setup_password(
    body: PasswordBody,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    values = await crud.get_settings(db)
    if values.get("master_password_hash"):
        raise HTTPException(status_code=409, detail="Master password is already configured.")
    if error := _password_error(body.password):
        raise HTTPException(status_code=422, detail=error)
    salt = secrets.token_bytes(16)
    await crud.update_settings(db, {
        "master_password_salt": salt.hex(),
        "master_password_hash": _derive(body.password, salt),
    })
    _new_session(request, response)
    return ok({"initialized": True, "authenticated": True})


@router.post("/login")
async def login(
    body: PasswordBody,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    values = await crud.get_settings(db)
    salt_hex, expected = values.get("master_password_salt"), values.get("master_password_hash")
    if not salt_hex or not expected:
        raise HTTPException(status_code=409, detail="Set up a master password first.")
    try:
        actual = _derive(body.password, bytes.fromhex(salt_hex))
    except ValueError:
        raise HTTPException(status_code=500, detail="Stored authentication settings are invalid.")
    if not hmac.compare_digest(actual, expected):
        raise HTTPException(status_code=401, detail="Incorrect master password.")
    _new_session(request, response)
    return ok({"authenticated": True})


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    sessions = getattr(request.app.state, "auth_sessions", {})
    if isinstance(sessions, dict):
        sessions.pop(token, None)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return ok({"authenticated": False})


@router.post("/change-password")
async def change_password(
    body: ChangePasswordBody,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    await require_authenticated(request, db)
    values = await crud.get_settings(db)
    salt_hex, expected = values.get("master_password_salt"), values.get("master_password_hash")
    if not salt_hex or not expected:
        raise HTTPException(status_code=409, detail="Master password is not configured.")
    if not hmac.compare_digest(_derive(body.current_password, bytes.fromhex(salt_hex)), expected):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    if error := _password_error(body.new_password):
        raise HTTPException(status_code=422, detail=error)
    salt = secrets.token_bytes(16)
    await crud.update_settings(db, {
        "master_password_salt": salt.hex(),
        "master_password_hash": _derive(body.new_password, salt),
    })
    sessions = getattr(request.app.state, "auth_sessions", {})
    if isinstance(sessions, dict):
        sessions.clear()
    _new_session(request, response)
    return ok({"changed": True})
