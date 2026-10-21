"""Filesystem create/modify/delete collector using watchdog."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Iterable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from backend.collectors.base import BaseCollector, make_event
from backend.config import PROJECT_ROOT

_DEFAULT_EXCLUDED = {".pyc", ".pyo", ".tmp", ".swp", ".log", ".bak"}
_INTERNAL_DIRECTORIES = {"evidence", ".venv", "__pycache__", ".git"}


class _Handler(FileSystemEventHandler):
    def __init__(
        self,
        buffer: list[dict[str, Any]],
        lock: threading.Lock,
        excluded: set[str],
        project_root: Path = PROJECT_ROOT,
        demo_path: Path | None = None,
    ):
        self.buffer = buffer
        self.lock = lock
        self.excluded = {ext.lower() for ext in excluded}
        self.project_root = project_root.resolve()
        self.demo_path = demo_path.resolve() if demo_path else None

    def _is_internal(self, path: Path) -> bool:
        """Exclude generated/repository trees while allowing the designated demo tree."""
        try:
            parts = path.resolve().relative_to(self.project_root).parts
        except (OSError, ValueError):
            return False
        lowered = tuple(part.lower() for part in parts)
        if self.demo_path is not None:
            try:
                path.resolve().relative_to(self.demo_path)
                in_demo_tree = True
            except (OSError, ValueError):
                in_demo_tree = False
            if in_demo_tree and not any(part in _INTERNAL_DIRECTORIES for part in lowered):
                return False
        if any(part in _INTERNAL_DIRECTORIES for part in lowered):
            return True
        # data/ is generated application state, except for the user-facing demo folder.
        return "data" in lowered and not (len(lowered) >= 2 and lowered[:2] == ("data", "monitored"))

    def _push(self, src_path: str, kind: str) -> None:
        path = Path(src_path).expanduser().resolve()
        if self._is_internal(path):
            return
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
        self.demo_path = (PROJECT_ROOT / "data" / "monitored").resolve()
        self.demo_path.mkdir(parents=True, exist_ok=True)
        self.handler = _Handler(self._buffer, self._lock, self._excluded, demo_path=self.demo_path)
        self.observer = Observer()
        self._watch_count = 0
        candidates = [*paths, self.demo_path]
        watched: set[Path] = set()
        for raw_path in candidates:
            if not raw_path or not str(raw_path).strip():
                continue
            try:
                path = Path(str(raw_path).strip()).expanduser().resolve()
                if path in watched:
                    continue
                if not path.is_dir():
                    self.logger.warning("monitored path is not an existing directory: %s", path)
                    continue
                self.observer.schedule(self.handler, str(path), recursive=True)
                watched.add(path)
                self._watch_count += 1
            except (OSError, RuntimeError, ValueError) as exc:
                self.logger.warning("cannot watch monitored path %s: %s", raw_path, exc)
                continue
        if self._watch_count == 0:
            self.logger.warning("file collector has no valid watch paths")

    def start(self) -> None:
        if not self.enabled or self._watch_count == 0:
            return
        if not self.observer.is_alive():
            try:
                self.observer.start()
            except (OSError, PermissionError) as exc:
                # A recursively watched user directory may contain protected
                # subdirectories even when its root is readable. Recover with
                # the guaranteed, app-owned demo directory so startup remains
                # useful and safe on a non-elevated Windows account.
                self.logger.warning(
                    "configured file watch failed (%s); retrying only the demo directory %s",
                    exc,
                    self.demo_path,
                )
                try:
                    self.observer.stop()
                    self.observer.join(timeout=2)
                except RuntimeError:
                    pass
                self.observer = Observer()
                try:
                    self.observer.schedule(self.handler, str(self.demo_path), recursive=True)
                    self.observer.start()
                    self._watch_count = 1
                except (OSError, PermissionError, RuntimeError) as fallback_error:
                    self.mark_unavailable(
                        f"cannot start even the local demo file watch at {self.demo_path}: {fallback_error}"
                    )

    def stop(self) -> None:
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=2)

    async def collect(self) -> list[dict[str, Any]]:
        with self._lock:
            events = list(self._buffer)
            self._buffer.clear()
        return events
