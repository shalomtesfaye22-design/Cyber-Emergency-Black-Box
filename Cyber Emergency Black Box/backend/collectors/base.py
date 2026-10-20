"""Shared collector contract for local, read-only endpoint telemetry."""

from __future__ import annotations

import logging
import socket
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

IngestCallback = Callable[[dict[str, Any]], Awaitable[Any]]

SEVERITIES = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def hostname() -> str:
    """Best-effort local hostname for event metadata."""
    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def make_event(
    event_type: str,
    source: str,
    *,
    user_name: str | None = None,
    process_name: str | None = None,
    action: str | None = None,
    target: str | None = None,
    source_ip: str | None = None,
    destination_ip: str | None = None,
    destination_port: int | None = None,
    protocol: str | None = None,
    severity: str = "INFO",
    metadata: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Build a collector payload that matches the shared ingestion schema."""
    extra = dict(metadata or {})
    extra.setdefault("hostname", hostname())
    extra.setdefault("is_simulated", False)
    level = (severity or "INFO").upper()
    if level not in SEVERITIES:
        level = "INFO"
    return {
        "timestamp": timestamp or utc_now(),
        "event_type": event_type,
        "source": source,
        "user_name": user_name,
        "process_name": process_name,
        "action": action or event_type,
        "target": target,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "destination_port": destination_port,
        "protocol": protocol,
        "severity": level,
        "metadata": extra,
        "is_simulated": False,
    }


class BaseCollector(ABC):
    """Abstract collector that feeds raw event dicts into the ingest callback."""

    name: str = "base"
    supported_platforms: tuple[str, ...] = ("Windows", "Linux", "Darwin")

    def __init__(self, ingest_callback: IngestCallback, enabled: bool = True):
        self.ingest_callback = ingest_callback
        self.ingest = ingest_callback
        self.enabled = enabled
        self.available = True
        self.logger = logging.getLogger(f"collectors.{self.name}")
        self.poll_interval = 0
        self._last_run = 0.0

    def current_platform(self) -> str:
        import platform

        return platform.system()

    def is_platform_supported(self) -> bool:
        return self.current_platform() in self.supported_platforms

    def mark_unavailable(self, reason: str) -> None:
        """Disable future collection cycles after a persistent failure."""
        if self.available:
            self.logger.warning("%s collector unavailable: %s", self.name, reason)
        self.available = False

    def _due_to_poll(self) -> bool:
        if self.poll_interval <= 0:
            return True
        now = time.monotonic()
        if now - self._last_run < self.poll_interval:
            return False
        self._last_run = now
        return True

    @abstractmethod
    async def collect(self) -> list[dict[str, Any]]:
        """Collect raw events from the local host. Return [] when unsupported."""

    async def run_once(self) -> None:
        if not self.enabled or not self.available or not self._due_to_poll():
            return
        if not self.is_platform_supported():
            self.mark_unavailable(f"unsupported platform {self.current_platform()}")
            return
        try:
            events = await self.collect() or []
            for raw in events:
                await self.ingest_callback(raw)
        except Exception as exc:
            self.logger.warning("collector error: %s", exc, exc_info=False)
