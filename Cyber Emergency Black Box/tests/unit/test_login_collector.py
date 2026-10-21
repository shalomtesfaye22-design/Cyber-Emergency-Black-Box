"""Portable tests for Windows log timestamp and permission handling."""

from datetime import datetime, timezone

from backend.collectors.login_collector import _is_access_denied, _local_to_utc


def test_login_event_timestamp_is_timezone_aware_utc():
    converted = _local_to_utc(datetime(2025, 1, 1, 12, 0, 0))
    assert converted.tzinfo is timezone.utc


def test_login_collector_recognizes_access_denied():
    assert _is_access_denied(PermissionError("access denied"))
    assert _is_access_denied(OSError(5, "access denied"))
    assert _is_access_denied(OSError(1314, "required privilege not held"))
    assert not _is_access_denied(OSError(2, "not found"))
