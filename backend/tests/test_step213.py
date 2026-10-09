"""Step 213: canonical source provenance reference and identity coherence."""

from datetime import datetime, timezone
import hashlib

import pytest

from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_provenance import (
    SourceProvenance,
    SourceProvenanceResult,
)
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder
from backend.app.reality.source_provenance_normalizer import (
    SourceProvenanceResultNormalizer,
)


A = "https://example.test/original-a"
B = "https://example.test/original-b"
NOW = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


def _hash(uri):
    return hashlib.sha256(uri.encode("utf-8")).hexdigest()


def _source(uri=A, source_id=None):
    return SourceProvenance(
        source_id=_hash(uri) if source_id is None else source_id,
        source_ref=uri,
        uri=uri,
        title="Source",
    )


def _usable_mapping(sources):
    return {
        "status": "usable",
        "sources": [source.to_dict() for source in sources],
        "source_count": len(sources),
        "provenance_executed": True,
        "reason": None,
    }


def test_builder_emits_normalized_uri_ref_and_stable_digest():
    result = SourceProvenanceBuilder().build_result({
        "status": "usable",
        "sources": [{"uri": "  " + A + " ", "title": "Original"}],
    })
    assert result.status == "usable"
    assert result.source_count == 1
    source = result.sources[0]
    assert (source.uri, source.source_ref, source.source_id) == (A, A, _hash(A))


@pytest.mark.parametrize("source_ref, uri", [
    (A, B),
    (B, A),
    (" " + A, A),
    (A, " " + A),
    (" " + A + " ", " " + A + " "),
    (A, A + " "),
])
def test_direct_provenance_rejects_mismatched_or_padded_uri_identity(
    source_ref, uri
):
    with pytest.raises(ValueError, match="must match the canonical source URI"):
        SourceProvenance(
            source_id="legacy-id", source_ref=source_ref, uri=uri
        )


@pytest.mark.parametrize("source_ref, uri", [
    (A, B),
    (" " + A, A),
    (A, A + " "),
])
def test_mapping_reconstruction_rejects_incoherent_source_identity(
    source_ref, uri
):
    mapping = _usable_mapping((_source(),))
    mapping["sources"][0]["source_ref"] = source_ref
    mapping["sources"][0]["uri"] = uri
    with pytest.raises(ValueError, match="must match the canonical source URI"):
        SourceProvenanceResult.validate(mapping)
    with pytest.raises(ValueError, match="must match the canonical source URI"):
        SourceProvenanceResultNormalizer.normalize(mapping)


def test_distinct_uris_cannot_claim_the_same_source_id():
    sources = (_source(A, "same-id"), _source(B, "same-id"))
    with pytest.raises(ValueError, match="source_ids must be unique"):
        SourceProvenanceResult.usable_result(sources)


def test_duplicate_source_refs_cannot_be_reported_as_distinct_sources():
    sources = (_source(A, "id-one"), _source(A, "id-two"))
    with pytest.raises(ValueError, match="source_refs must be unique"):
        SourceProvenanceResult.usable_result(sources)


@pytest.mark.parametrize("identity_collision", ["id", "ref"])
def test_mapping_and_normalizer_both_reject_identity_collisions(
    identity_collision
):
    if identity_collision == "id":
        sources = (_source(A, "id"), _source(B, "id"))
        reason = "source_ids must be unique"
    else:
        sources = (_source(A, "id-a"), _source(A, "id-b"))
        reason = "source_refs must be unique"
    mapping = _usable_mapping(sources)
    with pytest.raises(ValueError, match=reason):
        SourceProvenanceResult.validate(mapping)
    with pytest.raises(ValueError, match=reason):
        SourceProvenanceResultNormalizer.normalize(mapping)


def test_two_distinct_sources_roundtrip_with_canonical_identity():
    sources = (_source(A), _source(B))
    result = SourceProvenanceResult.usable_result(sources)
    assert result.source_count == 2
    assert SourceProvenanceResult.validate(result) is result
    assert SourceProvenanceResult.validate(result.to_dict()) == result
    assert SourceProvenanceResultNormalizer.normalize(result.to_dict()) == result


def test_historical_non_hash_source_id_remains_allowed_as_documented():
    # This step validates distinct identity keys and URI/ref equality, not
    # hash authenticity for legacy direct constructors used in earlier tests.
    record = _source(A, "source-1")
    assert record.source_id == "source-1"
    assert SourceProvenanceResult.usable_result((record,)).status == "usable"


def test_duplicate_uri_aliases_are_merged_before_building_valid_provenance():
    result = SourceProvenanceBuilder().build_result({
        "status": "usable",
        "sources": [
            {"uri": A, "title": "First"},
            {"uri": " " + A + " ", "title": "Alias"},
        ],
    })
    assert result.status == "usable"
    assert result.source_count == 1
    assert result.sources[0].source_id == _hash(A)


def test_invalid_mapping_is_rejected_before_downstream_observation():
    mapping = _usable_mapping((_source(A, "id"), _source(B, "id")))
    with pytest.raises(ValueError, match="source_ids must be unique"):
        SourceObservationBuilder(clock=lambda: NOW).build_result(mapping)
    with pytest.raises(ValueError, match="source_ids must be unique"):
        SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
            mapping,
            [
                {"uri": A, "observed_at": "2025-01-01T00:00:00Z"},
                {"uri": B, "observed_at": "2025-01-01T00:00:00Z"},
            ],
            require_provider_observations=True,
        )


def test_valid_provenance_still_generates_one_observation_per_source():
    result = SourceProvenanceResult.usable_result((_source(A), _source(B)))
    observations = SourceObservationBuilder(clock=lambda: NOW).build_retrieval_result(
        result,
        [
            {"uri": A, "observed_at": "2025-01-01T00:00:00Z"},
            {"uri": B, "observed_at": "2025-01-02T00:00:00Z"},
        ],
        require_provider_observations=True,
    )
    assert observations.status == "usable"
    assert observations.source_count == 2
    assert {item.source_id for item in observations.observations} == {
        _hash(A), _hash(B)
    }


def test_empty_and_unavailable_provenance_contracts_remain_supported():
    assert SourceProvenanceResult.empty_result().status == "empty"
    unavailable = SourceProvenanceResult.unavailable_result("evidence_not_usable")
    assert unavailable.status == "unavailable"
    assert unavailable.sources == ()


def test_provenance_refs_agree_with_claim_links_after_deduplication():
    evidence = {
        "status": "usable",
        "sources": [
            {"uri": " " + A + " ", "content": "Shared statement."},
            {"uri": B, "content": "Shared statement."},
        ],
        "content": "Shared statement.\n\nShared statement.",
    }
    claims = EvidenceClaimExtractor().extract_result(evidence)
    links = ClaimEvidenceLinker().link_result(claims, evidence)
    provenance = SourceProvenanceBuilder().build_result(evidence)
    assert claims.claims[0].source_refs == (A, B)
    assert provenance.status == "usable"
    assert {link.source_ref for link in links.links} == {
        source.source_ref for source in provenance.sources
    } == {A, B}


def test_end_to_end_submitted_state_still_has_distinct_provenance_and_links():
    state = build_reality_state_from_evidence(
        "What does the evidence say about Company X?",
        [
            {"uri": A, "content": "Company X announced Feature A."},
            {"uri": B, "content": "Company X announced Feature A."},
        ],
        entity="Company X",
    )
    assert state["claims"]["status"] == "usable"
    assert state["claims"]["claims"][0]["source_refs"] == [A, B]
    sources = state["source_provenance"]["sources"]
    assert len(sources) == 2
    assert {item["source_id"] for item in sources} == {_hash(A), _hash(B)}
    assert {item["source_ref"] for item in sources} == {A, B}
    assert {item["source_ref"] for item in state["claim_evidence_linking"]["links"]} == {A, B}
    assert state["source_observation"]["status"] == "usable"
