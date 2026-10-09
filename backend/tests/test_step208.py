"""Step 208: preserve semantic claims after global submitted-evidence deduplication."""

from dataclasses import replace

import pytest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.claim_semantic_structure import ClaimSemanticStructure
from backend.app.reality.submitted_evidence import (
    MAX_SUBMITTED_CLAIMS,
    SubmittedEvidenceBundle,
)


SOURCE_A = "https://example.test/official"
SOURCE_B = "https://example.test/report"
SOURCE_C = "https://example.test/archive"
SHARED = "Company X launched Feature A."
OTHER = "Company Y adopted Feature B."


class RecordingStructurer:
    def __init__(self, *, fail_on: str | None = None, malformed_on: str | None = None):
        self.calls = []
        self.fail_on = fail_on
        self.malformed_on = malformed_on

    def structure(self, claim_text, source_refs):
        self.calls.append((claim_text, source_refs))
        if claim_text == self.fail_on:
            raise RuntimeError("adapter failed")
        if claim_text == self.malformed_on:
            return {"status": "structured"}
        if claim_text == SHARED:
            return ClaimSemanticStructure.structured(
                subject="Company X",
                predicate="launched",
                object="Feature A",
                structuring_method="test_adapter",
            )
        return ClaimSemanticStructure.unstructured("unsupported_sentence")


def _bundle(documents):
    return SubmittedEvidenceBundle.from_mappings(documents)


def _sample_docs():
    return [
        {"uri": SOURCE_A, "content": SHARED + " " + OTHER},
        {"uri": SOURCE_B, "content": SHARED},
    ]


def test_semantic_structure_survives_cross_document_merge():
    adapter = RecordingStructurer()
    result = _bundle(_sample_docs()).extract_claims(EvidenceClaimExtractor(adapter))

    assert result.status == "usable"
    assert result.source_count == 2
    assert len(result.claims) == 2
    shared, other = result.claims

    assert shared.text == SHARED
    assert shared.source_refs == (SOURCE_A, SOURCE_B)
    assert shared.extraction_method == "deterministic_sentence_split"
    assert shared.semantic_structure.status == "structured"
    assert shared.semantic_structure.subject == "Company X"
    assert shared.semantic_structure.object == "Feature A"

    assert other.text == OTHER
    assert other.source_refs == (SOURCE_A,)
    assert other.semantic_structure.status == "unstructured"
    assert other.semantic_structure.reason == "unsupported_sentence"


def test_semantic_adapter_called_once_with_complete_source_lineage():
    adapter = RecordingStructurer()
    _bundle(_sample_docs()).extract_claims(EvidenceClaimExtractor(adapter))
    assert adapter.calls == [
        (SHARED, (SOURCE_A, SOURCE_B)),
        (OTHER, (SOURCE_A,)),
    ]


def test_multi_source_default_semantics_and_source_refs_remain_compatible():
    result = _bundle(_sample_docs()).extract_claims(EvidenceClaimExtractor())
    assert [claim.text for claim in result.claims] == [SHARED, OTHER]
    assert [claim.source_refs for claim in result.claims] == [
        (SOURCE_A, SOURCE_B),
        (SOURCE_A,),
    ]
    assert all(
        claim.semantic_structure == ClaimSemanticStructure.unstructured()
        for claim in result.claims
    )


def test_casefold_duplicates_preserve_first_claim_text_and_lineage():
    adapter = RecordingStructurer()
    docs = [
        {"uri": SOURCE_A, "content": SHARED},
        {"uri": SOURCE_B, "content": SHARED.lower()},
        {"uri": SOURCE_C, "content": SHARED},
    ]
    result = _bundle(docs).extract_claims(EvidenceClaimExtractor(adapter))
    assert len(result.claims) == 1
    assert result.claims[0].text == SHARED
    assert result.claims[0].source_refs == (SOURCE_A, SOURCE_B, SOURCE_C)
    assert result.claims[0].semantic_structure.status == "structured"
    assert adapter.calls == [
        (SHARED, (SOURCE_A, SOURCE_B, SOURCE_C))
    ]


@pytest.mark.parametrize("failure_mode", ["exception", "malformed"])
def test_one_bad_semantic_result_does_not_erase_merged_source_refs(failure_mode):
    adapter = RecordingStructurer(
        fail_on=SHARED if failure_mode == "exception" else None,
        malformed_on=SHARED if failure_mode == "malformed" else None,
    )
    result = _bundle(_sample_docs()).extract_claims(EvidenceClaimExtractor(adapter))
    claim = result.claims[0]
    assert claim.text == SHARED
    assert claim.source_refs == (SOURCE_A, SOURCE_B)
    assert claim.semantic_structure == ClaimSemanticStructure.unstructured(
        "semantic_structuring_failed"
    )
    assert result.claims[1].semantic_structure.reason == "unsupported_sentence"


def test_global_overbudget_rejects_before_any_structuring_call():
    # Each individual document is valid and individually below the limit.
    # Together they have one extra unique claim.
    first = " ".join(f"Fact {i}." for i in range(1_000))
    second = " ".join(f"Fact {i}." for i in range(1_000, MAX_SUBMITTED_CLAIMS + 1))
    adapter = RecordingStructurer()
    result = _bundle([
        {"uri": SOURCE_A, "content": first},
        {"uri": SOURCE_B, "content": second},
    ]).extract_claims(EvidenceClaimExtractor(adapter))
    assert result.status == "unavailable"
    assert result.reason == "submitted_claim_limit_exceeded"
    assert result.claims == ()
    assert result.source_count == 2
    assert adapter.calls == []


def test_exact_budget_with_duplicates_is_valid_before_adapter_runs():
    adapter = RecordingStructurer()
    content = " ".join(f"Fact {i}." for i in range(MAX_SUBMITTED_CLAIMS))
    result = _bundle([
        {"uri": SOURCE_A, "content": content},
        {"uri": SOURCE_B, "content": content},
    ]).extract_claims(EvidenceClaimExtractor(adapter))
    assert result.status == "usable"
    assert len(result.claims) == MAX_SUBMITTED_CLAIMS
    assert len(adapter.calls) == MAX_SUBMITTED_CLAIMS
    assert adapter.calls[0][1] == (SOURCE_A, SOURCE_B)
    assert adapter.calls[-1][1] == (SOURCE_A, SOURCE_B)


def test_invalid_extractor_rejected_as_before():
    with pytest.raises(ValueError, match="EvidenceClaimExtractor"):
        _bundle(_sample_docs()).extract_claims(object())


def test_real_reality_state_pipeline_preserves_structured_claim_and_evidence_links():
    adapter = RecordingStructurer()
    dependencies = replace(
        OrchestrationDependencies.default(),
        claim_extractor=EvidenceClaimExtractor(adapter),
    )
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        _sample_docs(),
        entity="Company X",
        dependencies=dependencies,
    )
    claims = state["claims"]["claims"]
    shared = claims[0]
    assert shared["text"] == SHARED
    assert shared["source_refs"] == [SOURCE_A, SOURCE_B]
    assert shared["semantic_structure"]["status"] == "structured"
    assert shared["semantic_structure"]["subject"] == "Company X"
    assert shared["semantic_structure"]["object"] == "Feature A"
    assert state["source_provenance"]["status"] == "usable"
    assert state["claim_evidence_linking"]["status"] == "usable"
    assert state["entity"]["name"] == "Company X"
    assert adapter.calls == [
        (SHARED, (SOURCE_A, SOURCE_B)),
        (OTHER, (SOURCE_A,)),
    ]


def test_unconfigured_real_reality_state_remains_honestly_unstructured():
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        _sample_docs(),
    )
    claim = state["claims"]["claims"][0]
    assert claim["source_refs"] == [SOURCE_A, SOURCE_B]
    assert claim["semantic_structure"]["status"] == "unstructured"
    assert claim["semantic_structure"]["reason"] == "semantic_structuring_not_attempted"
