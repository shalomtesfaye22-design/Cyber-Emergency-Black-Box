"""Common response envelopes and serialization utilities."""

from typing import Any


def ok(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Format standard API response envelope: {'data': ..., 'meta': ...}."""
    return {"data": data, "meta": meta or {}}
