import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.correlation.engine import CorrelationEngine
from backend.correlation.rules.account_compromise import AccountCompromiseRule
from backend.correlation.rules.file_activity import FileActivityRule
from backend.correlation.rules.suspicious_process import SuspiciousProcessRule
from backend.database import crud
from backend.models.event import NormalisedEvent


def event(kind, seconds, **extra):
    return NormalisedEvent(
        event_type=kind,
        source="test",
        timestamp=datetime.now(timezone.utc) + timedelta(seconds=seconds),
        **extra,
    )


def test_account_compromise_rule_fires():
    rows = [event("login_failure", i, user_name="a") for i in range(3)] + [
        event("login_success", 4, user_name="a"),
        event("process_start", 5, user_name="a"),
    ]
    assert AccountCompromiseRule().evaluate(rows)


def test_account_compromise_requires_follow_up_within_full_sequence_window():
    rows = [event("login_failure", i, user_name="a") for i in range(3)]
    rows += [event("login_success", 4, user_name="a"), event("process_start", 601, user_name="a")]
    assert AccountCompromiseRule().evaluate(rows) is None

    rows[-1] = event("process_start", 599, user_name="a")
    assert AccountCompromiseRule().evaluate(rows) is not None


def test_suspicious_process_requires_process_attribution():
    rule = SuspiciousProcessRule()
    rows = [
        event("process_start", 0),
        event("file_modified", 1, process_name="unknown.exe"),
        event("file_created", 2, process_name="unknown.exe"),
        event("network_connection", 3, process_name="unknown.exe"),
    ]
    assert rule.evaluate(rows) is None


def test_file_activity_requires_five_events():
    assert not FileActivityRule().evaluate([event("file_modified", i) for i in range(4)])
    assert FileActivityRule().evaluate([event("file_modified", i) for i in range(5)])


def test_suspicious_process_rule():
    rule = SuspiciousProcessRule()
    # Process starts, touches 2 files, then opens network connection
    ev1 = event("process_start", 1, process_name="malware.exe")
    ev2 = event("file_modified", 2, process_name="malware.exe", target="C:\\secret.txt")
    ev3 = event("file_created", 3, process_name="malware.exe", target="C:\\exfil.zip")
    ev4 = event("network_connection", 4, process_name="malware.exe", destination_ip="198.51.100.1")

    res = rule.evaluate([ev1, ev2, ev3, ev4])
    assert res is not None
    assert res.rule_id == "R-02"
    assert res.severity == "HIGH"
    assert len(res.event_ids) == 4

    # Without network connection, rule should not fire
    assert rule.evaluate([ev1, ev2, ev3]) is None


@pytest.mark.asyncio
async def test_correlation_engine_run_once_and_deduplication(db_session: AsyncSession):
    engine = CorrelationEngine()
    now = datetime.now(timezone.utc)

    # Ingest a sequence triggering account compromise
    events = [
        {
            "event_id": f"corr-ev-{i}",
            "timestamp": now + timedelta(seconds=i),
            "event_type": "login_failure",
            "source": "test",
            "user_name": "target_user",
        }
        for i in range(3)
    ]
    events.append({
        "event_id": "corr-ev-success",
        "timestamp": now + timedelta(seconds=4),
        "event_type": "login_success",
        "source": "test",
        "user_name": "target_user",
    })
    events.append({
        "event_id": "corr-ev-proc",
        "timestamp": now + timedelta(seconds=5),
        "event_type": "process_start",
        "source": "test",
        "user_name": "target_user",
        "process_name": "cmd.exe",
    })

    await crud.insert_events_bulk(db_session, events)

    # First correlation run should create 1 incident
    created = await engine.run_once(db_session)
    assert len(created) == 1
    inc = created[0]
    assert inc.rule_id == "R-01"
    assert inc.event_count == 5
    assert inc.interpretation is not None

    # Clean up preserved evidence on disk for this incident
    from backend.config import PROJECT_ROOT
    if inc.evidence_path:
        ev_dir = PROJECT_ROOT / inc.evidence_path
        if ev_dir.exists():
            shutil.rmtree(ev_dir, ignore_errors=True)

    # Second correlation run on the exact same events should duplicate-check and create 0
    second_run = await engine.run_once(db_session)
    assert len(second_run) == 0

