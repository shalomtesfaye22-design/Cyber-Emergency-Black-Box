from datetime import datetime, timedelta, timezone
from backend.models.event import NormalisedEvent
from backend.correlation.rules.rules import AccountCompromiseRule, FileActivityRule

def event(kind, seconds, **extra): return NormalisedEvent(event_type=kind,source="test",timestamp=datetime.now(timezone.utc)+timedelta(seconds=seconds),**extra)
def test_account_compromise_rule_fires():
    rows=[event("login_failure",i,user_name="a") for i in range(3)]+[event("login_success",4,user_name="a"),event("process_start",5,user_name="a")]
    assert AccountCompromiseRule().evaluate(rows)
def test_file_activity_requires_five_events():
    assert not FileActivityRule().evaluate([event("file_modified",i) for i in range(4)])
    assert FileActivityRule().evaluate([event("file_modified",i) for i in range(5)])
