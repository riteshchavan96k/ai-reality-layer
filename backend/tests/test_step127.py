import hashlib

import pytest

from backend.app.reality.source_provenance import SourceProvenance, SourceProvenanceResult
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder


def test_source_provenance_is_immutable_and_serializable():
    record = SourceProvenance(
        source_id=hashlib.sha256(b"https://example.com").hexdigest(),
        source_ref="https://example.com",
        uri="https://example.com",
        title="Example",
    )
    assert record.to_dict()["source_id"] == hashlib.sha256(b"https://example.com").hexdigest()
    with pytest.raises(Exception):
        record.uri = "changed"


def test_builder_assigns_deterministic_identity_from_exact_uri():
    result = SourceProvenanceBuilder().build_result(
        {
            "status": "usable",
            "sources": [{"title": "Example", "uri": "https://example.com/page"}],
            "content": "Evidence.",
        }
    )
    assert isinstance(result, SourceProvenanceResult)
    assert result.status == "usable"
    source = result.sources[0]
    assert source.source_ref == "https://example.com/page"
    assert source.source_id == hashlib.sha256(b"https://example.com/page").hexdigest()


def test_builder_preserves_title_and_does_not_normalize_uri():
    uri = "https://example.com/a?b=2&a=1"
    source = SourceProvenanceBuilder().build_result(
        {"status": "usable", "sources": [{"title": "T", "uri": uri}]}
    ).sources[0]
    assert source.uri == uri
    assert source.source_ref == uri
    assert source.title == "T"


def test_builder_deduplicates_exact_source_refs_only():
    result = SourceProvenanceBuilder().build_result(
        {
            "status": "usable",
            "sources": [
                {"uri": "https://example.com"},
                {"uri": "https://example.com"},
                {"uri": "https://example.com/"},
            ],
        }
    )
    assert result.source_count == 2
    assert [source.source_ref for source in result.sources] == [
        "https://example.com",
        "https://example.com/",
    ]


def test_builder_fails_closed_for_non_usable_evidence():
    result = SourceProvenanceBuilder().build_result(
        {"status": "invalid_evidence", "reason": "no_evidence", "sources": []}
    )
    assert result.status == "unavailable"
    assert result.reason == "no_evidence"


def test_builder_rejects_missing_uri_for_usable_source():
    with pytest.raises(ValueError, match="non-empty uri"):
        SourceProvenanceBuilder().build_result(
            {"status": "usable", "sources": [{"title": "No URI"}]}
        )


def test_builder_rejects_malformed_input():
    with pytest.raises(ValueError, match="evidence must be a dictionary"):
        SourceProvenanceBuilder().build_result("invalid")


def test_result_rejects_inconsistent_states():
    source = SourceProvenance("id", "uri", "uri")
    with pytest.raises(ValueError, match="usable source provenance requires"):
        SourceProvenanceResult("usable")
    with pytest.raises(ValueError, match="empty source provenance cannot"):
        SourceProvenanceResult("empty", sources=(source,))
    with pytest.raises(ValueError, match="requires a reason"):
        SourceProvenanceResult("unavailable")
