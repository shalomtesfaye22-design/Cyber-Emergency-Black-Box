from datetime import datetime, timezone
import pytest
from backend.collectors.normaliser import NormalisationError, normalise

def test_normalise_hashes_valid_event():
    event=normalise({"timestamp":datetime.now(timezone.utc),"event_type":"login_failure","source":"test"})
    assert event.raw_hash and event.event_id

def test_normalise_rejects_unknown_event_type():
    with pytest.raises(NormalisationError): normalise({"timestamp":datetime.now(timezone.utc),"event_type":"invalid","source":"test"})
