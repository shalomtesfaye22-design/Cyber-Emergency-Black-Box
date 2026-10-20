"""Startup registry for enabled endpoint collectors."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

from backend.collectors.base import BaseCollector
from backend.collectors.file_collector import FileCollector
from backend.collectors.login_collector import LoginCollector
from backend.collectors.network_collector import NetworkCollector
from backend.collectors.process_collector import ProcessCollector
from backend.collectors.system_info_collector import SystemInfoCollector
from backend.collectors.usb_collector import USBCollector

COLLECTOR_NAMES = ("system_info", "process", "network", "file", "login", "usb")


def parse_enabled_names(enabled_names: Any) -> set[str]:
    """Accept JSON lists, comma-separated strings, or already-parsed sequences."""
    if enabled_names is None:
        return set()
    if isinstance(enabled_names, (list, tuple, set)):
        return {str(name).strip() for name in enabled_names if str(name).strip()}
    text = str(enabled_names).strip()
    if not text:
        return set()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return {str(name).strip() for name in parsed if str(name).strip()}
    return {part.strip() for part in text.split(",") if part.strip()}


def _excluded_extensions() -> list[str]:
    try:
        from backend.config import settings

        return [part.strip() for part in str(settings.file_exclude_extensions).split(",") if part.strip()]
    except Exception:
        return [".pyc", ".pyo", ".tmp", ".swp", ".log", ".bak"]


def get_enabled_collectors(
    ingest: Callable,
    enabled_names: Any,
    paths: Iterable[str] = (),
) -> list[BaseCollector]:
    """Instantiate collectors listed in settings, preserving ingest callback wiring."""
    names = parse_enabled_names(enabled_names)
    factories: dict[str, Callable[[], BaseCollector]] = {
        "system_info": lambda: SystemInfoCollector(ingest),
        "process": lambda: ProcessCollector(ingest),
        "network": lambda: NetworkCollector(ingest),
        "file": lambda: FileCollector(ingest, paths, excluded=_excluded_extensions()),
        "login": lambda: LoginCollector(ingest),
        "usb": lambda: USBCollector(ingest),
    }
    return [factories[name]() for name in COLLECTOR_NAMES if name in names]
