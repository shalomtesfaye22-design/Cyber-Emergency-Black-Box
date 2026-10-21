"""Integration test for the simulator subsystem (FR-052 - FR-056)."""

import pytest
from simulator.scenarios.account_compromise import AccountCompromiseScenario
from simulator.runner import run_scenario


@pytest.mark.asyncio
async def test_simulator_account_compromise_sequence():
    """Verify that SIM-001 scenario produces the expected synthetic events."""
    collected = []

    async def mock_ingest(event_data: dict):
        collected.append(event_data)

    scenario = AccountCompromiseScenario()
    await scenario.run(mock_ingest, delay=0.01)

    # FR-054 / SIM-001 sequence: 3 login_failure, 1 login_success, 1 process_start, 2 file_modified, 1 network_connection
    assert len(collected) == 8

    # FR-056: All events must be clearly labelled as simulated
    for item in collected:
        assert item["is_simulated"] is True
        assert item["source"] == "simulator"

    event_types = [x["event_type"] for x in collected]
    assert event_types == [
        "login_failure",
        "login_failure",
        "login_failure",
        "login_success",
        "process_start",
        "file_modified",
        "file_modified",
        "network_connection",
    ]


@pytest.mark.asyncio
async def test_simulator_runner_callback():
    """Verify runner.py run_scenario function with callback."""
    events = []

    async def ingest_cb(e):
        events.append(e)

    await run_scenario("account_compromise", ingest=ingest_cb, delay=0.01)
    assert len(events) == 8

