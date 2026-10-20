"""Filesystem create/modify/delete collector using watchdog."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Iterable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from backend.collectors.base import BaseCollector, make_event

_DEFAULT_EXCLUDED = {".pyc", ".pyo", ".tmp", ".swp", ".log", ".bak"}


class _Handler(FileSystemEventHandler):
    def __init__(self, buffer: list[dict[str, Any]], lock: threading.Lock, excluded: set[str]):
        self.buffer = buffer
        self.lock = lock
        self.excluded = {ext.lower() for ext in excluded}

    def _push(self, src_path: str, kind: str) -> None:
        path = Path(src_path)
        if path.suffix.lower() in self.excluded:
            return
        if path.name.endswith("~"):
            return
        event = make_event(
            kind,
            "file",
            action=kind,
            target=str(path),
            severity="INFO",
            metadata={"path": str(path), "name": path.name},
        )
        with self.lock:
            self.buffer.append(event)

    def on_created(self, event) -> None:
        if not event.is_directory:
            self._push(event.src_path, "file_created")

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self._push(event.src_path, "file_modified")

    def on_deleted(self, event) -> None:
        if not event.is_directory:
            self._push(event.src_path, "file_deleted")


class FileCollector(BaseCollector):
    """Watches configured paths and drains buffered filesystem events."""

    name = "file"

    def __init__(
        self,
        ingest_callback,
        paths: Iterable[str] = (),
        excluded: Iterable[str] = _DEFAULT_EXCLUDED,
        enabled: bool = True,
    ):
        super().__init__(ingest_callback, enabled)
        self.poll_interval = 0
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._excluded = {str(ext).lower() for ext in excluded if ext}
        self.handler = _Handler(self._buffer, self._lock, self._excluded)
        self.observer = Observer()
        self._watch_count = 0
        for raw_path in paths:
            path = Path(str(raw_path).strip()) if raw_path else None
            if path is None or not str(path):
                continue
            if not path.exists():
                self.logger.warning("monitored path does not exist: %s", path)
                continue
            self.observer.schedule(self.handler, str(path), recursive=True)
            self._watch_count += 1
        if self._watch_count == 0:
            self.logger.warning("file collector has no valid watch paths")

    def start(self) -> None:
        if not self.enabled or self._watch_count == 0:
            return
        if not self.observer.is_alive():
            self.observer.start()

    def stop(self) -> None:
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=2)

    async def collect(self) -> list[dict[str, Any]]:
        with self._lock:
            events = list(self._buffer)
            self._buffer.clear()
        return events
