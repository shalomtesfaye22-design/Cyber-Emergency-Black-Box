"""Tests for the printable academic forensic report."""

from datetime import datetime, timezone
from types import SimpleNamespace

from backend.reports.html_report import generate_html_report


def test_executive_report_includes_attribution_mapping_and_print_styles():
    incident = SimpleNamespace(
        incident_id="INC-20261025-0001",
        rule_id="R-01",
        rule_name="Possible Account Compromise",
        severity="HIGH",
        status="OPEN",
        detection_time="2026-10-25T12:00:00+00:00",
        summary="Observed suspicious login pattern",
    )
    event = SimpleNamespace(
        event_id="evt-1",
        timestamp=datetime(2026, 10, 25, 11, 59, tzinfo=timezone.utc),
        event_type="login_failure",
        user_name="analyst-test",
        process_name="winlogon.exe",
        target="local account",
        destination_ip=None,
        destination_port=None,
    )
    html = generate_html_report(
        incident,
        [event],
        {
            "confirmed_facts": ["Three failed logins were recorded."],
            "detection_result": "R-01 matched.",
            "interpretation": "Consistent with credential guessing; verify with the owner.",
            "recommendations": ["Verify the activity with the account owner."],
        },
        {"files": {"events.json": {"size_bytes": 10, "sha256": "a" * 64}}},
        system={"hostname": "DFIR-LAB", "os_name": "Windows", "os_version": "11"},
    )

    assert "INSA Cyber Talent Center" in html
    assert "5th Round Summer Camp 2026" in html
    assert "T1078" in html and "T1110" in html
    assert "@media print" in html
    assert "events.json" in html and "a" * 64 in html
    assert "credential guessing" in html


def test_report_escapes_untrusted_incident_text():
    incident = SimpleNamespace(
        incident_id="INC-X",
        rule_id="unknown",
        rule_name="Test",
        severity="LOW",
        status="OPEN",
        detection_time="now",
        summary="<script>alert(1)</script>",
    )
    html = generate_html_report(incident, [], {}, {}, system={})
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html
