"""Integration tests for FastAPI REST endpoints."""

from datetime import datetime, timezone
import httpx
import pytest


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    """Test /api/v1/health endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_list_events(client: httpx.AsyncClient):
    """Test POST /api/v1/events and GET /api/v1/events."""
    event_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "process_start",
        "source": "integration_test",
        "user_name": "charlie",
        "process_name": "cmd.exe",
        "severity": "LOW",
        "metadata": {"test": True},
    }
    # 1. Create event
    post_resp = await client.post("/api/v1/events", json=event_payload)
    assert post_resp.status_code == 200
    created = post_resp.json()["data"]
    assert created["event_id"] is not None
    assert created["process_name"] == "cmd.exe"
    assert created["raw_hash"] is not None

    # 2. List events
    get_resp = await client.get("/api/v1/events")
    assert get_resp.status_code == 200
    list_data = get_resp.json()
    assert len(list_data["data"]) >= 1
    assert list_data["meta"]["count"] >= 1

    # 3. Retrieve event by ID
    event_id = created["event_id"]
    single_resp = await client.get(f"/api/v1/events/{event_id}")
    assert single_resp.status_code == 200
    assert single_resp.json()["data"]["event_id"] == event_id

    # 4. Stats endpoint
    stats_resp = await client.get("/api/v1/events/stats")
    assert stats_resp.status_code == 200
    assert "process_start" in stats_resp.json()["data"]


@pytest.mark.asyncio
async def test_incidents_api_workflow(client: httpx.AsyncClient):
    """Test incident listing and status patching via API."""
    # First, list incidents (should be empty initially)
    list_resp = await client.get("/api/v1/incidents")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json()["data"], list)


@pytest.mark.asyncio
async def test_settings_api(client: httpx.AsyncClient):
    """Test GET and PUT /api/v1/settings."""
    # 1. Get settings
    get_resp = await client.get("/api/v1/settings")
    assert get_resp.status_code == 200
    settings = get_resp.json()["data"]
    assert "retention_minutes" in settings

    # 2. Update valid setting
    put_resp = await client.put(
        "/api/v1/settings", json={"retention_minutes": 45}
    )
    assert put_resp.status_code == 200
    updated = put_resp.json()["data"]
    assert str(updated["retention_minutes"]) == "45"

    # 3. Update with invalid setting key -> 422
    invalid_resp = await client.put(
        "/api/v1/settings", json={"malicious_key": "bad"}
    )
    assert invalid_resp.status_code == 422


@pytest.mark.asyncio
async def test_system_and_dashboard_endpoints(client: httpx.AsyncClient):
    """Test system info, status, and dashboard summary."""
    # System info
    info_resp = await client.get("/api/v1/system/info")
    assert info_resp.status_code == 200
    info_data = info_resp.json()["data"]
    assert "hostname" in info_data
    assert "os_name" in info_data

    # System status
    status_resp = await client.get("/api/v1/system/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()["data"]
    assert "uptime_seconds" in status_data

    # Dashboard summary
    summary_resp = await client.get("/api/v1/dashboard/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()["data"]
    assert "event_count" in summary_data
    assert "incident_count" in summary_data
    assert "highest_severity" in summary_data
