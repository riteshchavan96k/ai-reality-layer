"""Step 209 — semantic method state integrity and bounded metadata."""

from dataclasses import replace

import pytest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_extraction import ClaimExtractionResult
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.claim_semantic_structure import (
    ClaimSemanticStructure,
    MAX_CLAIM_STRUCTURING_METHOD_CHARS,
    MAX_CLAIM_SEMANTIC_REASON_CHARS,
)
from backend.app.reality.claim_semantic_structurer import (
    ClaimSemanticStructuringStage,
)


SOURCE = "https://example.test/company"
TEXT = "Company X launched Feature A."


def _structured_mapping(method="semantic_adapter"):
    return {
        "status": "structured",
        "subject": "Company X",
        "predicate": "launched",
        "object": "Feature A",
        "structuring_method": method,
        "reason": None,
    }


class MappingStructurer:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def structure(self, text, source_refs):
        self.calls.append((text, source_refs))
        return self.result


@pytest.mark.parametrize("method", [
    "not_attempted", " not_attempted ", "\tnot_attempted\n",
])
def test_structured_claim_rejects_reserved_method_after_normalization(method):
    with pytest.raises(ValueError, match="non-empty structuring method"):
        ClaimSemanticStructure.structured(
            subject="Company X", predicate="launched", object="Feature A",
            structuring_method=method,
        )


@pytest.mark.parametrize("method", [" not_attempted ", "\tnot_attempted\n"])
def test_canonical_mapping_rejects_normalized_reserved_method(method):
    with pytest.raises(ValueError, match="non-empty structuring method"):
        ClaimSemanticStructure.validate(_structured_mapping(method))


def test_valid_method_is_trimmed_without_changing_provided_identity():
    claim = ClaimSemanticStructure.validate(
        _structured_mapping("  trusted_semantic_adapter  ")
    )
    assert claim.structuring_method == "trusted_semantic_adapter"
    assert claim.status == "structured"
    assert claim.to_dict()["structuring_method"] == "trusted_semantic_adapter"


def test_method_at_limit_is_accepted_and_preserved():
    method = "m" * MAX_CLAIM_STRUCTURING_METHOD_CHARS
    result = ClaimSemanticStructure.validate(_structured_mapping(" " + method + " "))
    assert result.structuring_method == method
    assert len(result.to_dict()["structuring_method"]) == MAX_CLAIM_STRUCTURING_METHOD_CHARS


@pytest.mark.parametrize("input_form", ["typed", "mapping"])
def test_oversized_method_is_rejected(input_form):
    method = "m" * (MAX_CLAIM_STRUCTURING_METHOD_CHARS + 1)
    with pytest.raises(ValueError, match="claim structuring method must not exceed"):
        if input_form == "typed":
            ClaimSemanticStructure.structured(
                subject="Company X", predicate="launched", object="Feature A",
                structuring_method=method,
            )
        else:
            ClaimSemanticStructure.validate(_structured_mapping(method))


def test_unstructured_reason_at_limit_is_trimmed_and_preserved():
    reason = "r" * MAX_CLAIM_SEMANTIC_REASON_CHARS
    result = ClaimSemanticStructure.unstructured(" " + reason + " ")
    assert result.reason == reason
    assert len(result.to_dict()["reason"]) == MAX_CLAIM_SEMANTIC_REASON_CHARS


@pytest.mark.parametrize("input_form", ["typed", "mapping"])
def test_oversized_unstructured_reason_is_rejected(input_form):
    reason = "r" * (MAX_CLAIM_SEMANTIC_REASON_CHARS + 1)
    with pytest.raises(ValueError, match="claim semantic reason must not exceed"):
        if input_form == "typed":
            ClaimSemanticStructure.unstructured(reason)
        else:
            ClaimSemanticStructure.validate({
                "status": "unstructured",
                "subject": None,
                "predicate": None,
                "object": None,
                "structuring_method": "not_attempted",
                "reason": reason,
            })


def test_invalid_structured_adapter_method_fails_closed_with_original_source():
    adapter = MappingStructurer(_structured_mapping("  not_attempted  "))
    claim = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable", "sources": [{"uri": SOURCE}], "content": TEXT,
    }).claims[0]
    assert claim.text == TEXT
    assert claim.source_refs == (SOURCE,)
    assert claim.semantic_structure.status == "unstructured"
    assert claim.semantic_structure.reason == "semantic_structuring_failed"
    assert adapter.calls == [(TEXT, (SOURCE,))]


@pytest.mark.parametrize("reported", [
    _structured_mapping("m" * (MAX_CLAIM_STRUCTURING_METHOD_CHARS + 1)),
    {
        "status": "unstructured",
        "subject": None,
        "predicate": None,
        "object": None,
        "structuring_method": "not_attempted",
        "reason": "r" * (MAX_CLAIM_SEMANTIC_REASON_CHARS + 1),
    },
])
def test_invalid_adapter_metadata_never_enlarges_canonical_result(reported):
    stage = ClaimSemanticStructuringStage(MappingStructurer(reported))
    value = stage.structure_claim(TEXT, (SOURCE,))
    assert value.to_dict() == ClaimSemanticStructure.unstructured(
        "semantic_structuring_failed"
    ).to_dict()


def test_legacy_claims_still_use_default_no_attempt_state():
    claims = EvidenceClaimExtractor().extract_result({
        "status": "usable", "sources": [{"uri": SOURCE}], "content": TEXT
    })
    assert claims.claims[0].semantic_structure == ClaimSemanticStructure.unstructured()


def test_valid_semantic_mapping_survives_serialization():
    adapter = MappingStructurer(_structured_mapping("  trusted_adapter  "))
    claims = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable", "sources": [{"uri": SOURCE}], "content": TEXT
    })
    restored = ClaimExtractionResult.validate(claims.to_dict())
    assert restored.claims[0].semantic_structure.structuring_method == "trusted_adapter"
    assert restored.claims[0].source_refs == (SOURCE,)


def test_malformed_semantic_mapping_rejected_by_canonical_claim_validation():
    adapter = MappingStructurer(_structured_mapping())
    claims = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable", "sources": [{"uri": SOURCE}], "content": TEXT
    }).to_dict()
    claims["claims"][0]["semantic_structure"]["structuring_method"] = " not_attempted "
    with pytest.raises(ValueError, match="non-empty structuring method"):
        ClaimExtractionResult.validate(claims)


def test_submitted_reality_state_preserves_valid_bounded_semantics():
    adapter = MappingStructurer(_structured_mapping("  trusted_adapter  "))
    dependencies = replace(
        OrchestrationDependencies.default(),
        claim_extractor=EvidenceClaimExtractor(adapter),
    )
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        [{"uri": SOURCE, "content": TEXT}],
        entity="Company X",
        dependencies=dependencies,
    )
    claim = state["claims"]["claims"][0]
    assert claim["semantic_structure"]["status"] == "structured"
    assert claim["semantic_structure"]["structuring_method"] == "trusted_adapter"
    assert claim["source_refs"] == [SOURCE]
    assert state["entity"]["name"] == "Company X"


def test_submitted_reality_state_hides_invalid_adapter_metadata():
    adapter = MappingStructurer(_structured_mapping(" not_attempted "))
    dependencies = replace(
        OrchestrationDependencies.default(),
        claim_extractor=EvidenceClaimExtractor(adapter),
    )
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        [{"uri": SOURCE, "content": TEXT}],
        dependencies=dependencies,
    )
    claim = state["claims"]["claims"][0]
    assert claim["semantic_structure"]["status"] == "unstructured"
    assert claim["semantic_structure"]["reason"] == "semantic_structuring_failed"
    assert claim["source_refs"] == [SOURCE]
