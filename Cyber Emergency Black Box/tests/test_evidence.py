from pathlib import Path
import pytest
from backend.evidence.manager import EvidenceManager
def test_evidence_rejects_path_traversal():
    with pytest.raises(ValueError): EvidenceManager()._path("../../../bad")
