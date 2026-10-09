"""Step 212: consistent source URI identity across evidence and claim pipeline."""

import hashlib
import json
import pytest

from backend.app.orchestrator.orchestrator import build_reality_state
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.http_retrieval_provider import HttpRetrievalProvider
from backend.app.reality.source_observation_builder import SourceObservationBuilder
from backend.app.reality.source_provenance_builder import SourceProvenanceBuilder


A = "https://example.test/original-a"
B = "https://example.test/original-b"
ENDPOINT = "https://retrieval.example.test/search?q={query}"


class RecordingStructurer:
    def __init__(self):
        self.calls = []

    def structure(self, claim_text, source_refs):
        self.calls.append((claim_text, source_refs))
        return None


def _provider(payload):
    return HttpRetrievalProvider(ENDPOINT)._normalize_payload(
        payload, ENDPOINT.replace("{query}", "status")
    )


def _scoped_sources():
    return [
        {"uri": "  " + A + "  ", "content": "Unique A. Shared claim."},
        {"uri": "\t" + B + "\n", "content": "Unique B. Shared claim."},
    ]


def test_http_ingress_strips_source_uris_but_preserves_actual_content():
    result = _provider({"status": "completed", "sources": _scoped_sources()})
    assert result.status == "completed"
    assert [source["uri"] for source in result.sources] == [A, B]
    assert [source["content"] for source in result.sources] == [
        "Unique A. Shared claim.", "Unique B. Shared claim."
    ]
    assert result.content == "Unique A. Shared claim.\n\nUnique B. Shared claim."


@pytest.mark.parametrize("sources", [
    [{"uri": A, "content": "First."},
     {"uri": " " + A + " ", "content": "Second."}],
    [{"uri": "\t" + A + "  ", "content": "First."},
     {"uri": A + "\n", "content": "Second."}],
])
def test_http_ingress_rejects_duplicates_after_trimming(sources):
    result = _provider({"status": "completed", "sources": sources})
    assert result.status == "failed"
    assert result.reason == "duplicate_source_uri"


def test_provider_neutral_evidence_normalization_uses_canonical_uri_keys():
    result = RetrievalEvidenceNormalizer().normalize_result({
        "status": "completed",
        "sources": _scoped_sources(),
        "content": None,
    })
    assert result.status == "completed"
    assert result.source_count == 2
    assert [source["uri"] for source in result.sources] == [A, B]
    assert result.content == "Unique A. Shared claim.\n\nUnique B. Shared claim."


def test_provider_neutral_alias_collision_fails_closed():
    result = RetrievalEvidenceNormalizer().normalize_result({
        "status": "completed",
        "sources": [
            {"uri": A, "content": "First."},
            {"uri": " " + A + " ", "content": "Second."},
        ],
        "content": None,
    })
    assert result.status == "invalid_evidence"
    assert result.content is None


@pytest.mark.parametrize("status", ["usable", "completed"])
def test_claim_extractor_canonicalizes_uris_and_deduplicates_claims(status):
    sources = _scoped_sources()
    content = "Unique A. Shared claim.\n\nUnique B. Shared claim."
    result = EvidenceClaimExtractor().extract_result({
        "status": status, "sources": sources, "content": content,
    })
    assert result.status == "usable"
    assert result.source_count == 2
    assert [(claim.text, claim.source_refs) for claim in result.claims] == [
        ("Unique A.", (A,)),
        ("Shared claim.", (A, B)),
        ("Unique B.", (B,)),
    ]


def test_legacy_single_source_extraction_uses_canonical_uri():
    result = EvidenceClaimExtractor().extract_result({
        "status": "usable", "sources": [{"uri": "  " + A + "  "}],
        "content": "Legacy claim.",
    })
    assert result.claims[0].text == "Legacy claim."
    assert result.claims[0].source_refs == (A,)


def test_extractor_rejects_padded_duplicate_refs_before_adapter():
    adapter = RecordingStructurer()
    result = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable",
        "sources": [
            {"uri": A, "content": "First."},
            {"uri": " " + A + " ", "content": "Second."},
        ],
        "content": "First.\n\nSecond.",
    })
    assert result.status == "unavailable"
    assert result.reason == "duplicate_source_attribution"
    assert result.claims == ()
    assert adapter.calls == []


def test_semantic_adapter_receives_trimmed_complete_source_lineage():
    adapter = RecordingStructurer()
    result = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable",
        "sources": _scoped_sources(),
        "content": "Unique A. Shared claim.\n\nUnique B. Shared claim.",
    })
    assert result.status == "usable"
    assert adapter.calls == [
        ("Unique A.", (A,)),
        ("Shared claim.", (A, B)),
        ("Unique B.", (B,)),
    ]


def test_provenance_hash_uses_exact_same_canonical_uri():
    provenance = SourceProvenanceBuilder().build_result({
        "status": "usable", "sources": _scoped_sources(),
    })
    assert provenance.source_count == 2
    assert [source.uri for source in provenance.sources] == [A, B]
    assert [source.source_ref for source in provenance.sources] == [A, B]
    assert provenance.sources[0].source_id == hashlib.sha256(
        A.encode("utf-8")
    ).hexdigest()
    assert provenance.sources[1].source_id == hashlib.sha256(
        B.encode("utf-8")
    ).hexdigest()


def test_low_level_provenance_deduplicates_whitespace_uri_aliases():
    provenance = SourceProvenanceBuilder().build_result({
        "status": "usable",
        "sources": [{"uri": A}, {"uri": " " + A + " "}],
    })
    assert provenance.status == "usable"
    assert provenance.source_count == 1
    assert provenance.sources[0].uri == A


def test_links_and_provenance_references_agree_on_canonical_uri():
    evidence = {
        "status": "usable", "sources": _scoped_sources(),
        "content": "Unique A. Shared claim.\n\nUnique B. Shared claim.",
    }
    claims = EvidenceClaimExtractor().extract_result(evidence)
    links = ClaimEvidenceLinker().link_result(claims, evidence)
    provenance = SourceProvenanceBuilder().build_result(evidence)
    assert links.status == "usable"
    assert {(link.claim_text, link.source_ref) for link in links.links} == {
        ("Unique A.", A),
        ("Shared claim.", A),
        ("Unique B.", B),
        ("Shared claim.", B),
    }
    assert {link.source_ref for link in links.links} == {
        source.source_ref for source in provenance.sources
    }


def test_retrieval_observation_matches_canonical_provenance_even_on_raw_input():
    sources = [
        {"uri": " " + A, "observed_at": "2025-01-01T00:00:00Z"},
        {"uri": B + " ", "observed_at": "2025-01-02T00:00:00Z"},
    ]
    provenance = SourceProvenanceBuilder().build_result({
        "status": "usable", "sources": sources,
    })
    observations = SourceObservationBuilder().build_retrieval_result(
        provenance, sources, require_provider_observations=True
    )
    assert observations.status == "usable"
    assert len(observations.observations) == 2
    assert {
        observation.source_id for observation in observations.observations
    } == {source.source_id for source in provenance.sources}


def test_retrieval_observation_does_not_overwrite_canonical_alias_collisions():
    provenance = SourceProvenanceBuilder().build_result({
        "status": "usable", "sources": [{"uri": A}],
    })
    observations = SourceObservationBuilder().build_retrieval_result(
        provenance, [{"uri": A}, {"uri": " " + A + " "}],
    )
    assert observations.status == "unavailable"
    assert observations.reason == "retrieval_source_provenance_mismatch"


def test_trim_does_not_rewrite_distinct_url_meanings():
    first = A
    second = A + "/"
    evidence = {
        "status": "usable",
        "sources": [
            {"uri": " " + first, "content": "Shared."},
            {"uri": second + " ", "content": "Shared."},
        ],
        "content": "Shared.\n\nShared.",
    }
    result = EvidenceClaimExtractor().extract_result(evidence)
    assert result.status == "usable"
    assert result.claims[0].source_refs == (first, second)


def test_submitted_evidence_already_normalizes_uris_compatibly():
    from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle
    bundle = SubmittedEvidenceBundle.from_mappings([
        {"uri": " " + A + " ", "content": "One."},
        {"uri": " " + B + " ", "content": "Two."},
    ])
    result = bundle.extract_claims(EvidenceClaimExtractor())
    assert [claim.source_refs for claim in result.claims] == [(A,), (B,)]


def test_configured_http_full_reality_state_has_matching_claim_link_and_provenance(
    monkeypatch,
):
    payload = {
        "status": "completed",
        "sources": _scoped_sources(),
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            data = json.dumps(payload).encode("utf-8")
            assert len(data) <= limit
            return data

    monkeypatch.setenv("ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE", ENDPOINT)
    monkeypatch.setattr(
        "backend.app.reality.http_retrieval_provider.urlopen",
        lambda request, timeout: Response(),
    )
    state = build_reality_state("What is the current status of Company X?")
    assert state["evidence"]["status"] == "completed"
    assert [source["uri"] for source in state["evidence"]["sources"]] == [A, B]
    assert [source["uri"] for source in state["source_provenance"]["sources"]] == [
        A, B
    ]
    claims = {claim["text"]: claim for claim in state["claims"]["claims"]}
    assert claims["Shared claim."]["source_refs"] == [A, B]
    link_refs = {link["source_ref"] for link in state["claim_evidence_linking"]["links"]}
    provenance_refs = {
        source["source_ref"] for source in state["source_provenance"]["sources"]
    }
    assert link_refs == provenance_refs == {A, B}
    assert state["source_observation"]["status"] == "usable"
    assert state["status"] != "supported"
