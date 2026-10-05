"""Step 187 — submitted-evidence source content survives Reality State output."""

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.api.evidence_reality_state import EvidenceRealityStateRequest
from backend.app.api.reality_state import RealityStateResponse
from backend.app.main import app, reality_state_from_evidence
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.evidence_normalizer import RetrievalEvidenceNormalizer
from backend.app.reality.evidence_quality import EvidenceQualityValidator
from backend.app.reality.source_freshness_evaluator import SourceFreshnessEvaluator
from backend.app.reality.submitted_evidence import (
    MAX_SUBMITTED_CLAIMS,
    MAX_SUBMITTED_CONTENT_CHARS,
    SubmittedEvidenceBundle,
)


TASK = "What is the current status of Company X?"
A = "https://example.test/a"
B = "https://example.test/b"
C = "https://example.test/c"
NOW = datetime(2026, 1, 1, 13, tzinfo=timezone.utc)


def _documents():
    return [
        {
            "title": "First report",
            "uri": A,
            "content": " Shared update. Company X operates. ",
            "observed_at": "2026-01-01T12:30:00Z",
        },
        {
            "title": "Second report",
            "uri": B,
            "content": "\nShared update. not Company X operates.\n",
            "observed_at": "2026-01-01T12:40:00+00:00",
        },
    ]


def _state(documents=None, age=None):
    dependencies = replace(
        OrchestrationDependencies.default(),
        source_freshness_evaluator=SourceFreshnessEvaluator(clock=lambda: NOW),
    )
    return build_reality_state_from_evidence(
        TASK,
        _documents() if documents is None else documents,
        freshness_max_age_seconds=age,
        dependencies=dependencies,
    )


def _claims_from_evidence(evidence):
    return EvidenceClaimExtractor().extract_result(evidence).to_dict()


def test_document_source_mapping_preserves_original_text_not_timestamp_metadata():
    bundle = SubmittedEvidenceBundle.from_mappings(_documents())
    sources = [doc.source_dict() for doc in bundle.documents]
    assert sources == [
        {
            "title": "First report",
            "uri": A,
            "content": "Shared update. Company X operates.",
        },
        {
            "title": "Second report",
            "uri": B,
            "content": "Shared update. not Company X operates.",
        },
    ]


def test_bundle_evidence_contains_source_scopes_and_deterministic_join():
    bundle = SubmittedEvidenceBundle.from_mappings(_documents())
    evidence = bundle.to_evidence()
    assert evidence["status"] == "completed"
    assert evidence["source_count"] == 2
    assert evidence["has_content"] is True
    assert evidence["content"] == "\n\n".join(
        src["content"] for src in evidence["sources"]
    )
    assert [src["uri"] for src in evidence["sources"]] == [A, B]
    assert [src["title"] for src in evidence["sources"]] == [
        "First report", "Second report"
    ]
    assert all("observed_at" not in src for src in evidence["sources"])


def test_source_scoped_evidence_can_be_reextracted_independently():
    bundle = SubmittedEvidenceBundle.from_mappings(_documents())
    extracted = bundle.extract_claims(EvidenceClaimExtractor()).to_dict()
    reextracted = _claims_from_evidence(bundle.to_evidence())
    assert reextracted == extracted
    assert reextracted["status"] == "usable"
    assert reextracted["claim_count"] == 3
    assert reextracted["claims"][0]["source_refs"] == [A, B]
    assert reextracted["claims"][1]["source_refs"] == [A]
    assert reextracted["claims"][2]["source_refs"] == [B]


def test_final_reality_state_claims_reproduce_exactly_from_evidence():
    state = _state()
    assert state["claims"] == _claims_from_evidence(state["evidence"])
    assert state["claim_evidence_linking"]["linked_claim_count"] == 3
    assert state["conflicts"]["conflict_count"] == 1
    assert state["freshness"]["unknown_count"] == 2
    assert state["status"] == "uncertain"


def test_source_provenance_identities_still_match_original_uris():
    state = _state()
    refs = [entry["uri"] for entry in state["source_provenance"]["sources"]]
    assert refs == [A, B]
    assert state["source_provenance"]["source_count"] == 2
    assert {
        x["source_ref"] for x in state["claim_evidence_linking"]["links"]
    } == {A, B}


def test_explicit_freshness_uses_separate_observation_contract():
    state = _state(age=3600)
    assert state["freshness"]["fresh_count"] == 2
    assert state["freshness"]["stale_count"] == 0
    assert state["status"] == "uncertain"  # Explicit conflict persists.
    observations = state["source_observation"]["observations"]
    assert {
        x["observation_method"] for x in observations
    } == {"submitted_evidence_observation"}
    assert [x["observed_at"] for x in observations] == [
        "2026-01-01T12:30:00Z",
        "2026-01-01T12:40:00Z",
    ]
    assert state["claims"] == _claims_from_evidence(state["evidence"])


def test_mixed_sources_missing_timestamps_keep_ingestion_provenance():
    docs = _documents()
    del docs[1]["observed_at"]
    state = _state(documents=docs)
    assert {
        x["observation_method"]
        for x in state["source_observation"]["observations"]
    } == {
        "submitted_evidence_observation",
        "submitted_evidence_ingestion",
    }
    assert state["freshness"]["unknown_count"] == 2
    assert state["claims"] == _claims_from_evidence(state["evidence"])


def test_casefold_duplicates_in_multiple_documents_roundtrip():
    docs = [
        {"uri": A, "content": "A shared claim. Distinct A."},
        {"uri": B, "content": "a shared claim. Distinct B."},
        {"uri": C, "content": "A shared claim."},
    ]
    state = _state(documents=docs)
    assert state["claims"] == _claims_from_evidence(state["evidence"])
    assert state["claims"]["claim_count"] == 3
    assert state["claims"]["claims"][0]["source_refs"] == [A, B, C]
    assert state["claim_evidence_linking"]["linked_claim_count"] == 3
    assert len(state["claim_evidence_linking"]["links"]) == 5


def test_single_source_payload_keeps_legacy_extractability():
    docs = [{"uri": A, "content": " Company X remains operational. "}]
    state = _state(documents=docs)
    assert state["claims"] == _claims_from_evidence(state["evidence"])
    assert state["evidence"]["sources"][0]["content"] == (
        "Company X remains operational."
    )
    assert state["evidence"]["content"] == (
        "Company X remains operational."
    )


def test_whitespace_and_newlines_roundtrip_without_cross_source_splicing():
    docs = [
        {"uri": A, "content": " \nSource A first fact.\nA second fact.\t"},
        {"uri": B, "content": "\nSource B only fact.\n"},
    ]
    state = _state(documents=docs)
    assert state["claims"] == _claims_from_evidence(state["evidence"])
    by_text = {
        c["text"]: c["source_refs"] for c in state["claims"]["claims"]
    }
    assert by_text == {
        "Source A first fact.": [A],
        "A second fact.": [A],
        "Source B only fact.": [B],
    }


def test_provider_neutral_normalizer_accepts_submitted_canonical_evidence():
    evidence = SubmittedEvidenceBundle.from_mappings(
        _documents()
    ).to_evidence()
    normalized = RetrievalEvidenceNormalizer().normalize_result(evidence)
    assert normalized.status == "completed"
    assert normalized.content == evidence["content"]
    assert normalized.sources == evidence["sources"]
    assert normalized.source_count == 2
    assert EvidenceQualityValidator().validate_result(
        normalized.to_dict()
    ).status == "usable"
    assert _claims_from_evidence(evidence) == _claims_from_evidence(
        normalized.to_dict()
    )


def test_returned_canonical_json_has_auditable_source_scopes():
    state = _state()
    payload = json.loads(json.dumps(state, allow_nan=False))
    assert payload["evidence"]["sources"][0]["content"].startswith(
        "Shared update."
    )
    assert payload["evidence"]["sources"][1]["content"].endswith(
        "not Company X operates."
    )
    validated = RealityStateResponse.model_validate(payload)
    assert validated.status == "uncertain"
    assert validated.evidence["sources"] == payload["evidence"]["sources"]
    assert payload["claims"] == _claims_from_evidence(payload["evidence"])


def test_existing_http_handler_returns_reextractable_evidence():
    request = EvidenceRealityStateRequest(task=TASK, documents=_documents())
    state = reality_state_from_evidence(request)
    assert state["evidence"]["source_count"] == 2
    assert state["claims"] == _claims_from_evidence(state["evidence"])
    assert state["source_provenance"]["source_count"] == 2


def test_existing_api_routes_and_schemas_stay_separate():
    paths = {route.path for route in app.routes}
    assert "/api/v1/reality-state/evidence" in paths
    assert "/api/v1/reality-state" in paths
    schemas = app.openapi()["components"]["schemas"]
    assert "documents" in schemas["EvidenceRealityStateRequest"][
        "properties"
    ]
    assert "documents" not in schemas["RealityStateRequest"]["properties"]


def _many_claims(n):
    return " ".join(f"Fact number {i}." for i in range(n))


def test_exact_global_claim_budget_can_be_roundtripped():
    docs = [
        {"uri": A, "content": _many_claims(MAX_SUBMITTED_CLAIMS // 2)},
        {
            "uri": B,
            "content": " ".join(
                f"Fact number {i}."
                for i in range(
                    MAX_SUBMITTED_CLAIMS // 2, MAX_SUBMITTED_CLAIMS
                )
            ),
        },
    ]
    state = _state(documents=docs)
    assert state["claims"]["status"] == "usable"
    assert state["claims"]["claim_count"] == MAX_SUBMITTED_CLAIMS
    assert state["claims"] == _claims_from_evidence(state["evidence"])


def test_over_budget_state_returns_no_partial_graph():
    docs = [
        {"uri": A, "content": _many_claims(1_200)},
        {
            "uri": B,
            "content": " ".join(f"Fact number {i}." for i in range(
                1_200, MAX_SUBMITTED_CLAIMS + 1
            )),
        },
    ]
    state = _state(documents=docs)
    assert state["evidence"]["source_count"] == 2
    assert len(state["evidence"]["sources"]) == 2
    assert state["claims"]["status"] == "unavailable"
    assert state["claims"]["reason"] == "submitted_claim_limit_exceeded"
    assert state["claims"]["claims"] == []
    assert state["claim_evidence_linking"]["links"] == []
    assert state["status"] != "supported"


def test_per_source_content_limit_remains_enforced():
    docs = [{"uri": A, "content": "x" * (
        MAX_SUBMITTED_CONTENT_CHARS + 1
    )}]
    with pytest.raises(ValueError, match="too large"):
        _state(documents=docs)


def test_original_uri_validation_and_duplicate_prevention_remain_enforced():
    with pytest.raises(ValueError, match="uri must use http or https"):
        _state(documents=[{"uri": "file:///tmp/a", "content": "Bad."}])
    with pytest.raises(ValueError, match="unique"):
        _state(documents=[
            {"uri": A, "content": "Claim A."},
            {"uri": A, "content": "Claim B."},
        ])
