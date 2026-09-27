import hashlib

import pytest

from backend.app.reality.source_provenance import SourceProvenance, SourceProvenanceResult
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder
from backend.app.reality.source_provenance_normalizer import SourceProvenanceResultNormalizer


def test_step157_accepts_canonical_source_provenance_result():
    source = SourceProvenance(
        source_id=hashlib.sha256("https://example.com".encode()).hexdigest(),
        source_ref="https://example.com",
        uri="https://example.com",
        title="Example",
    )
    result = SourceProvenanceResult.usable_result((source,))

    assert SourceProvenanceResult.validate(result) is result


def test_step157_normalizes_mapping():
    source_id = hashlib.sha256("https://example.com".encode()).hexdigest()
    result = SourceProvenanceResultNormalizer.normalize(
        {
            "status": "usable",
            "sources": [
                {
                    "source_id": source_id,
                    "source_ref": "https://example.com",
                    "uri": "https://example.com",
                    "title": "Example",
                    "identity_method": "sha256_uri",
                }
            ],
            "source_count": 1,
            "provenance_executed": True,
            "reason": None,
        }
    )

    assert result.status == "usable"
    assert result.source_count == 1
    assert result.sources[0].source_id == source_id


def test_step157_rejects_missing_required_result_field():
    with pytest.raises(ValueError, match="missing required fields"):
        SourceProvenanceResult.validate(
            {
                "status": "usable",
                "sources": [],
                "source_count": 0,
            }
        )


def test_step157_rejects_malformed_nested_source():
    with pytest.raises(ValueError, match="source provenance is missing required fields"):
        SourceProvenanceResultNormalizer.normalize(
            {
                "status": "usable",
                "sources": [{"uri": "https://example.com"}],
                "source_count": 1,
                "provenance_executed": True,
                "reason": None,
            }
        )


def test_step157_rejects_source_count_mismatch():
    with pytest.raises(ValueError, match="source_count must match"):
        SourceProvenanceResultNormalizer.normalize(
            {
                "status": "empty",
                "sources": [],
                "source_count": 1,
                "provenance_executed": True,
                "reason": None,
            }
        )


def test_step157_builder_returns_canonical_validated_result():
    result = SourceProvenanceBuilder().build_result(
        {
            "status": "usable",
            "sources": [
                {"uri": "https://example.com", "title": "Example"},
                {"uri": "https://example.com", "title": "Duplicate"},
            ],
        }
    )

    assert isinstance(result, SourceProvenanceResult)
    assert result.status == "usable"
    assert result.source_count == 1
    assert result.sources[0].source_ref == "https://example.com"
