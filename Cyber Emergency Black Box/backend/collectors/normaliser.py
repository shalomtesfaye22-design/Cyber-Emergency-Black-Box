"""Conversion of collector payloads into canonical events."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.models.event import EventCreate, NormalisedEvent


class NormalisationError(ValueError):
    """Raised when a collector or simulator payload cannot be normalised."""


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def normalise(raw: dict, previous_hash: str | None = None) -> NormalisedEvent:
    """Validate a raw event dict and attach SHA-256 hash and previous_hash link."""
    if not isinstance(raw, dict):
        raise NormalisationError("raw event must be a dict")
    payload = dict(raw)
    payload.setdefault("metadata", {})
    payload.setdefault("severity", "INFO")
    prev = previous_hash if previous_hash is not None else payload.get("previous_hash")
    try:
        event = EventCreate.model_validate(payload)
    except Exception as exc:
        raise NormalisationError(str(exc)) from exc
    dumped = event.model_dump(mode="json")
    return NormalisedEvent(
        **dumped,
        raw_hash=hashlib.sha256(_canonical_json(dumped).encode("utf-8")).hexdigest(),
        previous_hash=prev,
    )

