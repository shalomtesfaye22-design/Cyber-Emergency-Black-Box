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
async def test_incidents_api_workflow(client: httpx.AsyncClient, db_session):
    """Test full incident workflow: listing, get by id, patch status, timeline, and report."""
    from backend.database import crud

    # 1. List initially
    list_resp = await client.get("/api/v1/incidents")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json()["data"], list)

    # 2. Insert test incident and linked event
    now = datetime.now(timezone.utc)
    incident_id = "INC-API-TEST-001"
    await crud.insert_incident(
        db_session,
        {
            "incident_id": incident_id,
            "detection_time": now,
            "rule_id": "R-01",
            "rule_name": "Test Api Rule",
            "severity": "HIGH",
            "status": "OPEN",
            "summary": "Integration incident test",
            "event_count": 1,
            "interpretation": {"confirmed_facts": ["Fact 1"], "detection_result": "Detection", "interpretation": "Interp", "recommendations": ["Rec 1"], "disclaimer": "Disclaimer"},
        },
    )
    await crud.insert_event(
        db_session,
        {
            "event_id": "api-inc-event-01",
            "timestamp": now,
            "event_type": "login_failure",
            "source": "api_test",
            "user_name": "bob",
        },
    )
    await crud.link_events_to_incident(db_session, incident_id, ["api-inc-event-01"])

    # 3. Retrieve incident detail
    detail_resp = await client.get(f"/api/v1/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["incident_id"] == incident_id
    assert detail["severity"] == "HIGH"
    assert len(detail["events"]) == 1

    # 4. Patch incident status
    patch_resp = await client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"status": "INVESTIGATING"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "INVESTIGATING"

    # 5. Get timeline
    timeline_resp = await client.get(f"/api/v1/incidents/{incident_id}/timeline")
    assert timeline_resp.status_code == 200
    assert isinstance(timeline_resp.json()["data"], list)

    # 6. Insert snapshot and get printable HTML report
    await crud.insert_system_snapshot(
        db_session,
        {
            "hostname": "test-forensic-box",
            "os_name": "Windows",
            "os_version": "11.0",
            "uptime_seconds": 3600,
            "captured_at": now,
        },
    )
    report_resp = await client.get(f"/api/v1/incidents/{incident_id}/report")
    assert report_resp.status_code == 200
    assert "text/html" in report_resp.headers["content-type"]
    assert incident_id in report_resp.text
    assert "test-forensic-box" in report_resp.text

    # 7. Preserve evidence package and test evidence endpoints
    import shutil
    from pathlib import Path
    from backend.evidence.manager import EvidenceManager
    mgr = EvidenceManager()
    folder_str = await mgr.preserve(db_session, incident_id)
    folder = Path(folder_str)

    try:
        # 7a. Get manifest
        ev_resp = await client.get(f"/api/v1/incidents/{incident_id}/evidence")
        assert ev_resp.status_code == 200
        assert ev_resp.json()["data"]["incident_id"] == incident_id

        # 7b. Verify evidence
        verify_resp = await client.get(f"/api/v1/incidents/{incident_id}/evidence/verify")
        assert verify_resp.status_code == 200
        assert verify_resp.json()["data"]["valid"] is True

        # 7c. Download evidence ZIP
        dl_resp = await client.get(f"/api/v1/incidents/{incident_id}/evidence/download")
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "application/zip"
        assert len(dl_resp.content) > 0
    finally:
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        zip_file = folder.with_suffix(".zip")
        if zip_file.exists():
            zip_file.unlink(missing_ok=True)

    # 8. Non-existent incident -> 404
    missing_resp = await client.get("/api/v1/incidents/INC-NON-EXISTENT")
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_simulator_endpoints(client: httpx.AsyncClient):
    """Test simulator scenario listing and triggering."""
    # List scenarios
    list_resp = await client.get("/api/v1/simulator/scenarios")
    assert list_resp.status_code == 200
    assert "account_compromise" in list_resp.json()["data"]

    # Trigger scenario
    run_resp = await client.post("/api/v1/simulator/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["data"]["started"] is True


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
