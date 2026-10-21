"""Periodic local system snapshot collector."""

from __future__ import annotations

import platform
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import psutil

from backend.collectors.base import BaseCollector, make_event


class SystemInfoCollector(BaseCollector):
    """Collects hostname, OS, CPU, memory, and uptime metadata."""

    name = "system_info"

    def __init__(self, ingest_callback, enabled: bool = True):
        super().__init__(ingest_callback, enabled)
        try:
            from backend.config import settings

            self.poll_interval = int(settings.system_info_interval)
        except Exception:
            self.poll_interval = 60

    def _snapshot_fields(self) -> dict[str, Any]:
        boot = psutil.boot_time()
        vm = psutil.virtual_memory()
        return {
            "hostname": platform.node(),
            "os_name": platform.system(),
            "os_version": platform.version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(vm.total / 1024**3, 2),
            "uptime_seconds": int(time.time() - boot),
            "platform": platform.platform(),
            "python": platform.python_version(),
        }

    async def snapshot(self) -> dict[str, Any]:
        """Return the dict stored in the system_snapshots table."""
        fields = self._snapshot_fields()
        return {
            "snapshot_id": str(uuid.uuid4()),
            "captured_at": datetime.now(timezone.utc),
            "hostname": fields["hostname"],
            "os_name": fields["os_name"],
            "os_version": fields["os_version"],
            "cpu_count": fields["cpu_count"],
            "memory_total_gb": fields["memory_total_gb"],
            "uptime_seconds": fields["uptime_seconds"],
            "metadata": {
                "python": fields["python"],
                "platform": fields["platform"],
            },
        }

    async def collect(self) -> list[dict[str, Any]]:
        fields = self._snapshot_fields()
        return [
            make_event(
                "system_info",
                self.name,
                action="system_info",
                target=fields["hostname"],
                severity="INFO",
                metadata=fields,
            )
        ]
