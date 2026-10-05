"""Step 185 — cap direct-submitted evidence claim expansion globally."""

import pytest

from backend.app.api.evidence_reality_state import (
    EvidenceDocumentInput,
    EvidenceRealityStateRequest,
)
from backend.app.main import reality_state_from_evidence
from backend.app.orchestrator.orchestrator import (
    build_reality_state_from_evidence,
)
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.retrieval_input_bounds import MAX_RETRIEVED_CLAIMS
from backend.app.reality.submitted_evidence import (
    MAX_SUBMITTED_CLAIMS,
    MAX_SUBMITTED_DOCUMENTS,
    SubmittedEvidenceBundle,
)


URI_A = "https://example.test/source-a"
URI_B = "https://example.test/source-b"


def _sentences(start: int, count: int) -> str:
    return " ".join(f"Document fact {i}." for i in range(start, start + count))


def _document(uri: str, start: int, count: int) -> dict:
    return {"uri": uri, "content": _sentences(start, count)}


def _claims(documents):
    return SubmittedEvidenceBundle.from_mappings(
        documents
    ).extract_claims(EvidenceClaimExtractor())


def test_submitted_global_budget_matches_existing_retrieved_claim_budget():
    assert MAX_SUBMITTED_CLAIMS == MAX_RETRIEVED_CLAIMS == 2_000


def test_single_document_with_exactly_two_thousand_claims_is_accepted():
    result = _claims([_document(URI_A, 0, MAX_SUBMITTED_CLAIMS)])
    assert result.status == "usable"
    assert len(result.claims) == MAX_SUBMITTED_CLAIMS
    assert result.claims[0].source_refs == (URI_A,)
    assert result.claims[-1].source_refs == (URI_A,)


def test_single_document_over_budget_is_unavailable_without_partial_claims():
    result = _claims([_document(URI_A, 0, MAX_SUBMITTED_CLAIMS + 1)])
    assert result.status == "unavailable"
    assert result.reason == "submitted_claim_limit_exceeded"
    assert result.source_count == 1
    assert result.claims == ()


def test_two_documents_at_global_limit_keep_exact_source_lineage():
    result = _claims([
        _document(URI_A, 0, 1_000),
        _document(URI_B, 1_000, 1_000),
    ])
    assert result.status == "usable"
    assert len(result.claims) == MAX_SUBMITTED_CLAIMS
    assert result.source_count == 2
    assert result.claims[999].source_refs == (URI_A,)
    assert result.claims[1000].source_refs == (URI_B,)


def test_two_documents_exceed_global_limit_without_partial_claims():
    result = _claims([
        _document(URI_A, 0, 1_000),
        _document(URI_B, 1_000, 1_001),
    ])
    assert result.status == "unavailable"
    assert result.reason == "submitted_claim_limit_exceeded"
    assert result.source_count == 2
    assert result.claims == ()


def test_repeat_claims_across_many_documents_do_not_consume_extra_budget():
    result = _claims([
        _document(URI_A, 0, MAX_SUBMITTED_CLAIMS),
        _document(URI_B, 0, MAX_SUBMITTED_CLAIMS),
    ])
    assert result.status == "usable"
    assert len(result.claims) == MAX_SUBMITTED_CLAIMS
    assert result.claims[0].source_refs == (URI_A, URI_B)
    assert result.claims[-1].source_refs == (URI_A, URI_B)


def test_duplicate_sentences_within_document_are_deduplicated():
    repeated = "Repeated evidence. " * (MAX_SUBMITTED_CLAIMS + 5)
    result = SubmittedEvidenceBundle.from_mappings(
        [{"uri": URI_A, "content": repeated}]
    ).extract_claims(EvidenceClaimExtractor())
    assert result.status == "usable"
    assert len(result.claims) == 1
    assert result.claims[0].source_refs == (URI_A,)


def test_casefold_duplicates_merge_without_exceeding_global_budget():
    result = _claims([
        {"uri": URI_A, "content": "Same source claim. Another claim."},
        {"uri": URI_B, "content": "same source claim. Another claim."},
    ])
    assert result.status == "usable"
    assert len(result.claims) == 2
    assert [c.source_refs for c in result.claims] == [
        (URI_A, URI_B), (URI_A, URI_B)
    ]


def test_over_budget_direct_reality_state_has_no_partial_links_or_support():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [_document(URI_A, 0, 1_200), _document(URI_B, 1_200, 801)],
    )
    assert state["evidence"]["status"] == "completed"
    assert state["source_provenance"]["status"] == "usable"
    assert state["claims"]["status"] == "unavailable"
    assert state["claims"]["reason"] == "submitted_claim_limit_exceeded"
    assert state["claims"]["claim_count"] == 0
    assert state["claims"]["claims"] == []
    assert state["claim_evidence_linking"]["links"] == []
    assert state["conflicts"]["conflicts"] == []
    assert state["status"] != "supported"


def test_over_budget_http_handler_returns_conservative_snapshot():
    request = EvidenceRealityStateRequest(
        task="What is the current status of Company X?",
        documents=[
            EvidenceDocumentInput(**_document(URI_A, 0, 1_001)),
            EvidenceDocumentInput(**_document(URI_B, 1_001, 1_000)),
        ],
    )
    result = reality_state_from_evidence(request)
    assert result["claims"]["status"] == "unavailable"
    assert result["claims"]["reason"] == "submitted_claim_limit_exceeded"
    assert result["claim_evidence_linking"]["links"] == []
    assert result["status"] != "supported"


def test_in_bounds_submitted_reality_state_still_links_each_source():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [
            {"uri": URI_A, "content": "Shared claim. Unique A."},
            {"uri": URI_B, "content": "Shared claim. Unique B."},
        ],
    )
    assert state["claims"]["status"] == "usable"
    assert state["claims"]["claim_count"] == 3
    by_text = {c["text"]: c["source_refs"] for c in state["claims"]["claims"]}
    assert by_text == {
        "Shared claim.": [URI_A, URI_B],
        "Unique A.": [URI_A],
        "Unique B.": [URI_B],
    }
    assert len(state["claim_evidence_linking"]["links"]) == 4


def test_freshness_and_conflict_handling_remains_compatible():
    state = build_reality_state_from_evidence(
        "What is the current status of Company X?",
        [
            {"uri": URI_A, "content": "Company X is operational."},
            {"uri": URI_B, "content": "not Company X is operational."},
        ],
    )
    assert state["conflicts"]["conflict_count"] == 1
    assert state["freshness"]["unknown_count"] == 2
    assert state["status"] == "uncertain"


def test_lazy_document_iterable_cannot_force_unbounded_materialization():
    seen = []

    def endless_documents():
        i = 0
        while True:
            seen.append(i)
            if i > MAX_SUBMITTED_DOCUMENTS:
                raise AssertionError("infinite input consumed past safety bound")
            yield {"uri": f"https://example.test/{i}", "content": "Claim."}
            i += 1

    with pytest.raises(ValueError, match="too many submitted evidence documents"):
        SubmittedEvidenceBundle.from_mappings(endless_documents())
    assert len(seen) == MAX_SUBMITTED_DOCUMENTS + 1


def test_document_count_at_limit_still_succeeds_from_lazy_iterable():
    def documents():
        for i in range(MAX_SUBMITTED_DOCUMENTS):
            yield {
                "uri": f"https://example.test/source-{i}",
                "content": "Shared claim.",
            }

    bundle = SubmittedEvidenceBundle.from_mappings(documents())
    assert len(bundle.documents) == MAX_SUBMITTED_DOCUMENTS
    result = bundle.extract_claims(EvidenceClaimExtractor())
    assert result.status == "usable"
    assert result.claims[0].source_refs == tuple(
        f"https://example.test/source-{i}"
        for i in range(MAX_SUBMITTED_DOCUMENTS)
    )


def test_low_level_usable_legacy_claim_extraction_is_not_redefined():
    # The existing lower-level legacy usable status is a separate contract.
    # This step bounds the developer-submission bundle, not every caller of
    # the generic extractor.
    content = _sentences(0, MAX_SUBMITTED_CLAIMS + 1)
    result = EvidenceClaimExtractor().extract_result({
        "status": "usable",
        "sources": [{"uri": URI_A}],
        "content": content,
    })
    assert result.status == "usable"
    assert len(result.claims) == MAX_SUBMITTED_CLAIMS + 1
