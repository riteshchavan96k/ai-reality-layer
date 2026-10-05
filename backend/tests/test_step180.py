import pytest

from backend.app.api.evidence_reality_state import (
    EvidenceDocumentInput,
    EvidenceRealityStateRequest,
)
from backend.app.api.reality_state import RealityStateRequest, RealityStateResponse
from backend.app.main import app, reality_state_from_evidence
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.submitted_evidence import (
    MAX_SUBMITTED_DOCUMENTS,
    SubmittedEvidenceBundle,
)


def _documents():
    return [
        {
            "title": "Company X official update",
            "uri": "https://example.test/company-x-official",
            "content": (
                "Company X launched Feature A today. "
                "Company X continues to operate."
            ),
        },
        {
            "title": "Independent report",
            "uri": "https://example.test/company-x-report",
            "content": (
                "Company X launched Feature A today. "
                "not Company X continues to operate."
            ),
        },
    ]


def test_submitted_evidence_request_is_bounded_and_source_scoped():
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=_documents(),
    )

    assert request.task == "What is the current status of Company X?"
    assert len(request.documents) == 2
    assert isinstance(request.documents[0], EvidenceDocumentInput)
    assert request.documents[0].uri == (
        "https://example.test/company-x-official"
    )


def test_submitted_evidence_request_rejects_invalid_or_ambiguous_input():
    with pytest.raises(Exception):
        EvidenceRealityStateRequest(
            task="   ",
            documents=_documents(),
        )

    with pytest.raises(Exception):
        EvidenceRealityStateRequest(
            task="task",
            documents=[],
        )

    with pytest.raises(Exception):
        EvidenceRealityStateRequest(
            task="task",
            documents=[
                {
                    "content": "Evidence.",
                    "uri": "ftp://example.test/source",
                }
            ],
        )

    duplicate = [
        {
            "content": "First.",
            "uri": "https://example.test/same",
        },
        {
            "content": "Second.",
            "uri": "https://example.test/same",
        },
    ]
    with pytest.raises(Exception, match="document uris must be unique"):
        EvidenceRealityStateRequest(
            task="task",
            documents=duplicate,
        )

    with pytest.raises(Exception):
        EvidenceRealityStateRequest(
            task="task",
            documents=_documents(),
            unexpected=True,
        )


def test_submitted_evidence_request_enforces_document_count_limit():
    documents = [
        {
            "content": f"Evidence {index}.",
            "uri": f"https://example.test/{index}",
        }
        for index in range(MAX_SUBMITTED_DOCUMENTS + 1)
    ]

    with pytest.raises(Exception):
        EvidenceRealityStateRequest(
            task="task",
            documents=documents,
        )


def test_bundle_preserves_source_scoped_claim_lineage():
    bundle = SubmittedEvidenceBundle.from_mappings(_documents())
    result = bundle.extract_claims(EvidenceClaimExtractor())

    claims = {claim.text: claim for claim in result.claims}

    shared = claims["Company X launched Feature A today."]
    assert shared.source_refs == (
        "https://example.test/company-x-official",
        "https://example.test/company-x-report",
    )

    positive = claims["Company X continues to operate."]
    assert positive.source_refs == (
        "https://example.test/company-x-official",
    )

    negative = claims["not Company X continues to operate."]
    assert negative.source_refs == (
        "https://example.test/company-x-report",
    )


def test_duplicate_claims_merge_source_refs_without_duplicate_claims():
    bundle = SubmittedEvidenceBundle.from_mappings(
        [
            {
                "content": "Shared claim.",
                "uri": "https://example.test/a",
            },
            {
                "content": "Shared claim.",
                "uri": "https://example.test/b",
            },
        ]
    )

    result = bundle.extract_claims(EvidenceClaimExtractor())

    assert len(result.claims) == 1
    assert result.claims[0].text == "Shared claim."
    assert result.claims[0].source_refs == (
        "https://example.test/a",
        "https://example.test/b",
    )


def test_direct_evidence_builds_multi_source_reality_state_with_conflict():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        _documents(),
    )

    assert state["status"] == "uncertain"
    assert state["evidence"]["status"] == "completed"
    assert state["evidence"]["source_count"] == 2

    claims = state["claims"]
    assert claims["status"] == "usable"
    assert claims["claim_count"] == 3
    assert claims["source_count"] == 2

    linking = state["claim_evidence_linking"]
    assert linking["status"] == "usable"
    assert linking["claim_count"] == 3
    assert linking["linked_claim_count"] == 3
    assert linking["unlinked_claim_count"] == 0
    assert len(linking["links"]) == 4

    provenance = state["source_provenance"]
    assert provenance["status"] == "usable"
    assert provenance["source_count"] == 2

    observation = state["source_observation"]
    assert observation["status"] == "usable"
    assert observation["source_count"] == 2

    freshness = state["freshness"]
    assert freshness["status"] == "usable"
    assert freshness["unknown_count"] == 2

    conflicts = state["conflicts"]
    assert conflicts["status"] == "usable"
    assert conflicts["conflict_count"] == 1

    confidence = state["confidence_signals"]
    assert confidence["status"] == "uncertain"
    assert confidence["claim_coverage"] == 1.0
    assert confidence["conflict_count"] == 1
    assert "candidate_conflicts_present" in confidence["signals"]
    assert "freshness_uncertain" in confidence["signals"]


def test_direct_evidence_path_does_not_call_retrieval_provider(
    monkeypatch,
):
    monkeypatch.setenv(
        "ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE",
        "https://retrieval.example.test/search?q={query}",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("direct evidence path must not perform retrieval")

    monkeypatch.setattr(
        "backend.app.reality.http_retrieval_provider.HttpRetrievalProvider.retrieve",
        fail_if_called,
    )

    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [_documents()[0]],
    )

    assert state["evidence"]["status"] == "completed"
    assert state["source_provenance"]["status"] == "usable"


def test_http_handler_uses_submitted_evidence_without_solve_or_retrieval():
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=_documents(),
    )

    state = reality_state_from_evidence(request)

    assert state["task"] == request.task
    assert state["claims"]["claim_count"] == 3
    assert state["source_provenance"]["source_count"] == 2


def test_original_reality_state_request_stays_separate_from_submitted_documents():
    # Step 183 adds an optional retrieval freshness policy but never accepts
    # direct source documents on this existing retrieval endpoint.
    assert set(RealityStateRequest.model_fields) == {
        "task", "freshness_max_age_seconds",
    }
    with pytest.raises(ValueError):
        RealityStateRequest(
            task="Current status?",
            documents=[{"uri": "https://example.test", "content": "Untrusted."}],
        )


def test_openapi_documents_direct_evidence_endpoint_and_shared_contracts():
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/reality-state/evidence"]["post"]

    request_ref = (
        operation["requestBody"]["content"]
        ["application/json"]["schema"]["$ref"]
    )
    response_ref = (
        operation["responses"]["200"]["content"]
        ["application/json"]["schema"]["$ref"]
    )
    validation_ref = (
        operation["responses"]["422"]["content"]
        ["application/json"]["schema"]["$ref"]
    )
    internal_ref = (
        operation["responses"]["500"]["content"]
        ["application/json"]["schema"]["$ref"]
    )

    assert request_ref.endswith("/EvidenceRealityStateRequest")
    assert response_ref.endswith("/RealityStateResponse")
    assert validation_ref.endswith("/ValidationErrorResponse")
    assert internal_ref.endswith("/InternalErrorResponse")
    assert "X-Request-ID" in operation["responses"]["200"]["headers"]
    assert "X-Request-ID" in operation["responses"]["422"]["headers"]
    assert "X-Request-ID" in operation["responses"]["500"]["headers"]


def test_direct_evidence_route_declares_canonical_response_model():
    route = next(
        route
        for route in app.routes
        if route.path == "/api/v1/reality-state/evidence"
    )

    assert route.response_model is RealityStateResponse
