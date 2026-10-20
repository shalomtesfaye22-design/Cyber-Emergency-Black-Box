"""Process start/stop collector using a pid inventory diff."""

from __future__ import annotations

from typing import Any

import psutil

from backend.collectors.base import BaseCollector, make_event


class ProcessCollector(BaseCollector):
    """Emits process_start / process_stop events from psutil snapshots."""

    name = "process"

    def __init__(self, ingest_callback, enabled: bool = True):
        super().__init__(ingest_callback, enabled)
        self._previous: dict[int, tuple[str, str | None]] = {}
        self._primed = False
        try:
            from backend.config import settings

            self.poll_interval = int(settings.process_poll_interval)
        except Exception:
            self.poll_interval = 5

    def _inventory(self) -> dict[int, tuple[str, str | None]]:
        current: dict[int, tuple[str, str | None]] = {}
        for proc in psutil.process_iter(["pid", "name", "username"]):
            info = proc.info
            pid = info.get("pid")
            if pid is None:
                continue
            current[int(pid)] = (info.get("name") or "unknown", info.get("username"))
        return current

    async def collect(self) -> list[dict[str, Any]]:
        try:
            current = self._inventory()
        except (psutil.Error, OSError) as exc:
            self.logger.warning("process inventory failed: %s", exc)
            return []

        if not self._primed:
            self._previous = current
            self._primed = True
            return []

        events: list[dict[str, Any]] = []
        previous_ids = set(self._previous)
        current_ids = set(current)

        for pid in current_ids - previous_ids:
            name, user = current[pid]
            events.append(
                make_event(
                    "process_start",
                    self.name,
                    user_name=user,
                    process_name=name,
                    action="process_start",
                    target=str(pid),
                    severity="INFO",
                    metadata={"pid": pid},
                )
            )

        for pid in previous_ids - current_ids:
            name, user = self._previous.get(pid, ("unknown", None))
            events.append(
                make_event(
                    "process_stop",
                    self.name,
                    user_name=user,
                    process_name=name,
                    action="process_stop",
                    target=str(pid),
                    severity="INFO",
                    metadata={"pid": pid},
                )
            )

        self._previous = current
        return events
