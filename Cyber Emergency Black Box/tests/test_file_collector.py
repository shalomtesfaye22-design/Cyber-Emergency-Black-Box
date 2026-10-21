"""Acceptance coverage for the guaranteed local file-collector demo path."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

from backend.collectors import file_collector as file_collector_module
from backend.collectors.file_collector import FileCollector
from backend.config import PROJECT_ROOT


def test_collector_resolves_user_paths_and_always_watches_demo_directory(monkeypatch):
    class RecordingObserver:
        def __init__(self):
            self.paths = []

        def schedule(self, handler, path, recursive):
            self.paths.append(Path(path))

        def is_alive(self):
            return False

    observer = RecordingObserver()
    monkeypatch.setattr(file_collector_module, "Observer", lambda: observer)

    collector = FileCollector(lambda _event: None, paths=["~"])

    assert Path.home().resolve() in observer.paths
    assert (PROJECT_ROOT / "data" / "monitored").resolve() in observer.paths
    assert collector.demo_path.is_dir()


def test_demo_directory_emits_file_lifecycle_events_and_filters_internal_paths():
    collector = FileCollector(lambda _event: None, paths=[])
    sample = collector.demo_path / "demo-file.txt"
    for method in (collector.handler.on_created, collector.handler.on_modified, collector.handler.on_deleted):
        method(SimpleNamespace(is_directory=False, src_path=str(sample)))

    internal = PROJECT_ROOT / "evidence" / "noise.txt"
    collector.handler.on_created(SimpleNamespace(is_directory=False, src_path=str(internal)))
    events = asyncio.run(collector.collect())

    assert [event["event_type"] for event in events] == [
        "file_created",
        "file_modified",
        "file_deleted",
    ]
    assert all(event["metadata"]["path"] == str(sample.resolve()) for event in events)


def test_permission_error_falls_back_to_demo_directory(monkeypatch):
    observers = []

    class FailingObserver:
        def __init__(self):
            self.paths = []
            self.alive = False
            observers.append(self)

        def schedule(self, handler, path, recursive):
            self.paths.append(Path(path))

        def start(self):
            if len(observers) == 1:
                raise PermissionError("protected descendant")
            self.alive = True

        def is_alive(self):
            return self.alive

        def stop(self):
            self.alive = False

        def join(self, timeout=None):
            return None

    monkeypatch.setattr(file_collector_module, "Observer", FailingObserver)
    collector = FileCollector(lambda _event: None, paths=[str(Path.home())])

    collector.start()

    assert len(observers) == 2
    assert observers[1].paths == [collector.demo_path]
    assert collector.observer.is_alive()
