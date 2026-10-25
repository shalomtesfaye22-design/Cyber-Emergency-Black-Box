"""API contract checks for fields consumed by the served dashboard."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import crud


@pytest.mark.asyncio
async def test_authentication_protects_api_and_supports_password_login(client: AsyncClient):
    status = (await client.get("/api/v1/auth/status")).json()["data"]
    assert status == {"initialized": True, "authenticated": True}

    assert (await client.post("/api/v1/auth/logout")).status_code == 200
    assert (await client.get("/api/v1/events/stats")).status_code == 401
    assert (await client.post("/api/v1/auth/login", json={"password": "wrong"})).status_code == 401
    assert (await client.post(
        "/api/v1/auth/login", json={"password": "Test-Password-42!"}
    )).status_code == 200


@pytest.mark.asyncio
async def test_first_run_rejects_weak_master_password(
    client: AsyncClient, db_session: AsyncSession
):
    await crud.update_settings(db_session, {"master_password_hash": "", "master_password_salt": ""})
    client.cookies.clear()
    client._transport.app.state.auth_sessions.clear()
    assert (await client.get("/api/v1/events/stats")).status_code == 423
    weak = await client.post("/api/v1/auth/setup", json={"password": "weak"})
    assert weak.status_code == 422
    assert "at least 8" in weak.json()["detail"]
    client._transport.app.state.auth_sessions = set()
    setup = await client.post(
        "/api/v1/auth/setup", json={"password": "Test-Password-42!"}
    )
    assert setup.status_code == 200
    assert isinstance(client._transport.app.state.auth_sessions, dict)


@pytest.mark.asyncio
async def test_dashboard_system_and_settings_contracts(client: AsyncClient):
    summary = (await client.get("/api/v1/dashboard/summary")).json()["data"]
    assert {"event_count", "incident_count", "highest_severity", "uptime_seconds", "monitoring_active"} <= summary.keys()

    host = (await client.get("/api/v1/system/info")).json()["data"]
    assert {"os_name", "os_version", "cpu_percent", "memory_percent", "boot_time"} <= host.keys()

    status = (await client.get("/api/v1/system/status")).json()["data"]
    assert status["status"] in {"operational", "degraded"}
    assert isinstance(status["collectors"], list)

    settings = (await client.get("/api/v1/settings")).json()["data"]
    assert "monitored_paths" in settings
    assert "master_password_hash" not in settings
    assert "master_password_salt" not in settings
    assert (await client.put("/api/v1/settings", json={"retention_minutes": 40})).status_code == 200
    assert (await client.put("/api/v1/settings", json={"collector_interval_seconds": 5})).status_code == 422


@pytest.mark.asyncio
async def test_event_filter_accepts_simulated_only_parameter(client: AsyncClient):
    base = {
        "event_type": "process_start",
        "source": "contract-test",
        "user_name": "contract-user",
        "process_name": "contract.exe",
        "action": "started",
    }
    assert (await client.post("/api/v1/events", json={**base, "is_simulated": False})).status_code == 200
    assert (await client.post("/api/v1/events", json={**base, "is_simulated": True})).status_code == 200
    response = await client.get("/api/v1/events", params={"simulated_only": "false"})
    assert response.status_code == 200
    assert all(not row["is_simulated"] for row in response.json()["data"])


@pytest.mark.asyncio
async def test_frontend_shell_loads_modular_assets(client: AsyncClient):
    page = await client.get("/")
    css = await client.get("/static/style.css")
    javascript = await client.get("/static/app.js")
    assert page.status_code == css.status_code == javascript.status_code == 200
    assert "/static/style.css" in page.text
    assert "/static/app.js" in page.text
    assert "async function route()" in javascript.text
