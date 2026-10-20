"""Established-connection collector using a connection inventory diff."""

from __future__ import annotations

from typing import Any

import psutil

from backend.collectors.base import BaseCollector, make_event

_LOOPBACK = {"127.0.0.1", "::1"}


def _addr_ip(addr) -> str | None:
    return getattr(addr, "ip", None) if addr else None


def _addr_port(addr) -> int | None:
    port = getattr(addr, "port", None) if addr else None
    return int(port) if port is not None else None


def _process_fields(pid: int | None) -> tuple[str | None, str | None]:
    if not pid:
        return None, None
    try:
        proc = psutil.Process(pid)
        return proc.name(), proc.username()
    except (psutil.Error, ValueError, OSError):
        return None, None


class NetworkCollector(BaseCollector):
    """Emits network_connection events for newly established inet sockets."""

    name = "network"

    def __init__(self, ingest_callback, enabled: bool = True):
        super().__init__(ingest_callback, enabled)
        self._previous: set[tuple] = set()
        self._primed = False
        self._access_warned = False
        try:
            from backend.config import settings

            self.poll_interval = int(settings.network_poll_interval)
        except Exception:
            self.poll_interval = 10

    def _connections(self) -> list[Any]:
        return psutil.net_connections(kind="inet")

    async def collect(self) -> list[dict[str, Any]]:
        try:
            conns = self._connections()
        except (psutil.Error, OSError) as exc:
            if not self._access_warned:
                self.logger.warning(
                    "network connections unavailable (often needs elevated rights): %s",
                    exc,
                )
                self._access_warned = True
            return []

        current: set[tuple] = set()
        fresh: list[Any] = []
        for conn in conns:
            if getattr(conn, "status", None) != psutil.CONN_ESTABLISHED:
                continue
            if not conn.raddr:
                continue
            source_ip = _addr_ip(conn.laddr)
            dest_ip = _addr_ip(conn.raddr)
            if source_ip in _LOOPBACK and dest_ip in _LOOPBACK:
                continue
            key = (
                conn.pid,
                source_ip,
                _addr_port(conn.laddr),
                dest_ip,
                _addr_port(conn.raddr),
            )
            current.add(key)
            if self._primed and key not in self._previous:
                fresh.append(conn)

        if not self._primed:
            self._previous = current
            self._primed = True
            return []

        events: list[dict[str, Any]] = []
        for conn in fresh:
            process_name, user_name = _process_fields(conn.pid)
            dest_port = _addr_port(conn.raddr)
            events.append(
                make_event(
                    "network_connection",
                    self.name,
                    user_name=user_name,
                    process_name=process_name,
                    action="network_connection",
                    target=str(conn.pid) if conn.pid is not None else None,
                    source_ip=_addr_ip(conn.laddr),
                    destination_ip=_addr_ip(conn.raddr),
                    destination_port=dest_port,
                    protocol="tcp",
                    severity="INFO",
                    metadata={
                        "pid": conn.pid,
                        "local_port": _addr_port(conn.laddr),
                        "status": conn.status,
                    },
                )
            )

        self._previous = current
        return events
