"""Conversion of collector payloads into canonical events."""
import hashlib, json
from backend.models.event import EventCreate, NormalisedEvent
class NormalisationError(ValueError): pass
def normalise(raw: dict) -> NormalisedEvent:
    try:
        event=EventCreate.model_validate(raw)
    except Exception as exc: raise NormalisationError(str(exc)) from exc
    payload=event.model_dump(mode="json")
    return NormalisedEvent(**payload, raw_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest())
