"""Read-only Windows Security log collector for logon success and failure."""

from __future__ import annotations

from datetime import datetime, timezone
import errno
from typing import Any

from backend.collectors.base import BaseCollector, make_event, utc_now

# Interactive / network / unlock / remote-interactive logon types.
_INTERESTING_LOGON_TYPES = {"2", "3", "7", "8", "10", "11"}
_SUCCESS_EVENT_ID = 4624
_FAILURE_EVENT_ID = 4625


def _local_to_utc(value: datetime | None) -> datetime:
    if value is None:
        return utc_now()
    if not isinstance(value, datetime):
        # pywin32 timestamp values are usually datetime subclasses. Accept
        # timestamp-like wrappers as well, keeping the resulting value UTC-aware.
        timestamp = getattr(value, "timestamp", None)
        if callable(timestamp):
            try:
                return datetime.fromtimestamp(timestamp(), tz=timezone.utc)
            except (OSError, OverflowError, TypeError, ValueError):
                return utc_now()
        return utc_now()
    if value.tzinfo is None:
        local_tz = datetime.now().astimezone().tzinfo
        value = value.replace(tzinfo=local_tz)
    return value.astimezone(timezone.utc)


def _is_access_denied(error: Exception) -> bool:
    """Recognize Windows access-denied errors and standard permission failures."""
    winerror = getattr(error, "winerror", None)
    error_code = error.args[0] if getattr(error, "args", ()) else None
    return (
        isinstance(error, PermissionError)
        or winerror in {5, 1314}  # access denied / required privilege not held
        or getattr(error, "errno", None) == errno.EACCES
        or error_code in {5, 1314}
    )


def _insert(inserts: list[Any] | tuple[Any, ...] | None, index: int) -> str | None:
    if not inserts or index >= len(inserts):
        return None
    item = inserts[index]
    if item is None:
        return None
    text = str(item).strip()
    return text or None


class LoginCollector(BaseCollector):
    """Collects login_success / login_failure from Windows Event IDs 4624 / 4625."""

    name = "login"
    supported_platforms = ("Windows",)

    def __init__(self, ingest_callback, enabled: bool = True):
        super().__init__(ingest_callback, enabled)
        self.poll_interval = 5
        self._last_record = 0
        self._primed = False
        self._win32evtlog = None
        if not self.is_platform_supported():
            self.mark_unavailable(f"login events require Windows, found {self.current_platform()}")
            return
        try:
            import win32evtlog  # type: ignore
        except ImportError:
            self.mark_unavailable("pywin32 unavailable; login collector disabled")
            return
        self._win32evtlog = win32evtlog

    def _open_log(self):
        return self._win32evtlog.OpenEventLog(None, "Security")

    def _prime_cursor(self) -> None:
        handle = self._open_log()
        try:
            oldest = self._win32evtlog.GetOldestEventLogRecord(handle)
            total = self._win32evtlog.GetNumberOfEventLogRecords(handle)
            self._last_record = max(0, int(oldest) + int(total) - 1)
            self._primed = True
        finally:
            self._win32evtlog.CloseEventLog(handle)

    def _iter_new_records(self) -> list[Any]:
        handle = self._open_log()
        flags = (
            self._win32evtlog.EVENTLOG_BACKWARDS_READ
            | self._win32evtlog.EVENTLOG_SEQUENTIAL_READ
        )
        collected: list[Any] = []
        try:
            while True:
                batch = self._win32evtlog.ReadEventLog(handle, flags, 0)
                if not batch:
                    break
                stop = False
                for record in batch:
                    record_number = int(getattr(record, "RecordNumber", 0) or 0)
                    if record_number <= self._last_record:
                        stop = True
                        break
                    collected.append(record)
                if stop:
                    break
        finally:
            self._win32evtlog.CloseEventLog(handle)
        collected.sort(key=lambda rec: int(getattr(rec, "RecordNumber", 0) or 0))
        return collected

    def _to_event(self, record: Any) -> dict[str, Any] | None:
        event_id = int(getattr(record, "EventID", 0) or 0) & 0xFFFF
        if event_id not in {_SUCCESS_EVENT_ID, _FAILURE_EVENT_ID}:
            return None
        inserts = getattr(record, "StringInserts", None)
        success = event_id == _SUCCESS_EVENT_ID
        if success:
            logon_type = _insert(inserts, 8)
            workstation = _insert(inserts, 11)
            process_name = _insert(inserts, 17)
            source_ip = _insert(inserts, 18)
            failure_reason = None
        else:
            logon_type = _insert(inserts, 10)
            workstation = _insert(inserts, 13)
            process_name = _insert(inserts, 18)
            source_ip = _insert(inserts, 19)
            failure_reason = _insert(inserts, 8)
        if logon_type and logon_type not in _INTERESTING_LOGON_TYPES:
            return None
        user_name = _insert(inserts, 5)
        domain = _insert(inserts, 6)
        if source_ip == "-":
            source_ip = None
        return make_event(
            "login_success" if success else "login_failure",
            self.name,
            user_name=user_name,
            process_name=process_name,
            action="login_success" if success else "login_failure",
            target=workstation or domain,
            source_ip=source_ip,
            severity="INFO" if success else "LOW",
            timestamp=_local_to_utc(getattr(record, "TimeGenerated", None)),
            metadata={
                "event_id": event_id,
                "record_number": getattr(record, "RecordNumber", None),
                "logon_type": logon_type,
                "domain": domain,
                "workstation": workstation,
                "failure_reason": failure_reason,
                "computer": getattr(record, "ComputerName", None),
            },
        )

    async def collect(self) -> list[dict[str, Any]]:
        if not self._win32evtlog:
            return []
        try:
            if not self._primed:
                self._prime_cursor()
                return []
            records = self._iter_new_records()
        except Exception as exc:
            if _is_access_denied(exc):
                self.mark_unavailable(
                    "access denied reading the Windows Security event log. "
                    "Run the demo from an elevated terminal or grant this account "
                    "Event Log Readers / Security log read rights."
                )
                return []
            self.logger.warning("login event log read failed: %s", exc)
            return []

        events: list[dict[str, Any]] = []
        for record in records:
            record_number = int(getattr(record, "RecordNumber", 0) or 0)
            if record_number > self._last_record:
                self._last_record = record_number
            event = self._to_event(record)
            if event:
                events.append(event)
        return events
