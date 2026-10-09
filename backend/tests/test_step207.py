"""Step 207 — provider-neutral, fail-closed semantic structuring boundary."""

from dataclasses import replace

import pytest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.claim_semantic_structure import ClaimSemanticStructure
from backend.app.reality.claim_semantic_structurer import (
    ClaimSemanticStructuringStage,
    NotAttemptedClaimSemanticStructurer,
)


SOURCE_A = "https://example.test/a"
SOURCE_B = "https://example.test/b"


class StaticStructurer:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def structure(self, claim_text, source_refs):
        self.calls.append((claim_text, source_refs))
        return self.result


class FailingStructurer:
    def structure(self, claim_text, source_refs):
        raise RuntimeError("provider unavailable")


class PerClaimStructurer:
    def structure(self, claim_text, source_refs):
        if claim_text.startswith("Bad"):
            raise RuntimeError("failed claim")
        return ClaimSemanticStructure.structured(
            subject="Company X",
            predicate="launched",
            object="Feature A",
            structuring_method="test_semantic_adapter",
        )


def _structured():
    return ClaimSemanticStructure.structured(
        subject="  Company X ",
        predicate=" launched ",
        object=" Feature A ",
        structuring_method=" test_semantic_adapter ",
    )


def _evidence(content="Company X launched Feature A."):
    return {
        "status": "usable",
        "sources": [{"uri": SOURCE_A}],
        "content": content,
    }


def test_default_stage_explicitly_does_not_attempt_semantics():
    stage = ClaimSemanticStructuringStage()
    value = stage.structure_claim("Company X launched Feature A.", (SOURCE_A,))
    assert isinstance(NotAttemptedClaimSemanticStructurer().structure("a", ()), ClaimSemanticStructure)
    assert value.to_dict() == ClaimSemanticStructure.unstructured().to_dict()


def test_existing_default_extractor_output_remains_unstructured():
    result = EvidenceClaimExtractor().extract_result(_evidence())
    assert result.status == "usable"
    assert result.claims[0].semantic_structure == ClaimSemanticStructure.unstructured()
    assert result.claims[0].to_dict()["source_refs"] == [SOURCE_A]


def test_typed_structurer_result_preserved_and_normalized():
    adapter = StaticStructurer(_structured())
    result = EvidenceClaimExtractor(adapter).extract_result(_evidence())
    assert result.claims[0].semantic_structure.status == "structured"
    assert result.claims[0].semantic_structure.subject == "Company X"
    assert result.claims[0].semantic_structure.predicate == "launched"
    assert result.claims[0].semantic_structure.structuring_method == "test_semantic_adapter"
    assert adapter.calls == [("Company X launched Feature A.", (SOURCE_A,))]


def test_mapping_shaped_result_validated_using_canonical_contract():
    adapter = StaticStructurer(_structured().to_dict())
    result = EvidenceClaimExtractor(adapter).extract_result(_evidence())
    assert result.claims[0].semantic_structure == _structured()


def test_explicit_adapter_abstention_remains_unstructured():
    adapter = StaticStructurer(ClaimSemanticStructure.unstructured("low_model_confidence"))
    claim = EvidenceClaimExtractor(adapter).extract_result(_evidence()).claims[0]
    assert claim.semantic_structure.status == "unstructured"
    assert claim.semantic_structure.reason == "low_model_confidence"


def test_none_result_fails_closed_with_explicit_reason():
    adapter = StaticStructurer(None)
    result = EvidenceClaimExtractor(adapter).extract_result(_evidence())
    assert result.claims[0].semantic_structure == ClaimSemanticStructure.unstructured(
        "semantic_structuring_no_result"
    )


@pytest.mark.parametrize(
    "bad_result",
    [
        "subject=Company X",
        {"status": "structured"},
        {
            "status": "structured",
            "subject": "Company X",
            "predicate": "",
            "object": "Feature A",
            "structuring_method": "test_adapter",
            "reason": None,
        },
        {
            "status": "unstructured",
            "subject": "Company X",
            "predicate": None,
            "object": None,
            "structuring_method": "not_attempted",
            "reason": "unknown",
        },
    ],
)
def test_malformed_adapter_output_fails_closed_without_losing_claim(bad_result):
    result = EvidenceClaimExtractor(StaticStructurer(bad_result)).extract_result(_evidence())
    assert result.claims[0].text == "Company X launched Feature A."
    assert result.claims[0].source_refs == (SOURCE_A,)
    assert result.claims[0].semantic_structure == ClaimSemanticStructure.unstructured(
        "semantic_structuring_failed"
    )


def test_adapter_exception_does_not_create_fake_semantics():
    result = EvidenceClaimExtractor(FailingStructurer()).extract_result(_evidence())
    claim = result.claims[0]
    assert claim.semantic_structure.status == "unstructured"
    assert claim.semantic_structure.reason == "semantic_structuring_failed"


def test_one_claim_failure_does_not_remove_another_claim():
    result = EvidenceClaimExtractor(PerClaimStructurer()).extract_result(
        _evidence("Good claim. Bad claim.")
    )
    assert len(result.claims) == 2
    assert result.claims[0].semantic_structure.status == "structured"
    assert result.claims[1].semantic_structure.status == "unstructured"
    assert result.claims[1].semantic_structure.reason == "semantic_structuring_failed"


def test_deduplication_happens_before_structuring_with_complete_source_lineage():
    adapter = StaticStructurer(_structured())
    result = EvidenceClaimExtractor(adapter).extract_result(
        {
            "status": "completed",
            "sources": [
                {"uri": SOURCE_A, "content": "Company X launched Feature A."},
                {"uri": SOURCE_B, "content": "Company X launched Feature A."},
            ],
            "content": (
                "Company X launched Feature A.\n\n"
                "Company X launched Feature A."
            ),
        }
    )
    assert len(result.claims) == 1
    assert result.claims[0].source_refs == (SOURCE_A, SOURCE_B)
    assert result.claims[0].semantic_structure.status == "structured"
    assert adapter.calls == [
        ("Company X launched Feature A.", (SOURCE_A, SOURCE_B))
    ]


def test_adapter_is_not_invoked_when_evidence_is_unavailable():
    adapter = StaticStructurer(_structured())
    result = EvidenceClaimExtractor(adapter).extract_result(
        {"status": "failed", "sources": []}
    )
    assert result.status == "unavailable"
    assert adapter.calls == []


def test_adapter_is_not_invoked_when_source_attribution_is_missing():
    adapter = StaticStructurer(_structured())
    result = EvidenceClaimExtractor(adapter).extract_result(
        {"status": "usable", "sources": [], "content": "Claim."}
    )
    assert result.status == "unavailable"
    assert adapter.calls == []


def test_invalid_structurer_configuration_is_rejected():
    with pytest.raises(ValueError, match="callable structure method"):
        EvidenceClaimExtractor(object())


@pytest.mark.parametrize(
    ("claim_text", "refs"),
    [("", (SOURCE_A,)), ("Claim.", []), ("Claim.", ()), ("Claim.", ("",))],
)
def test_stage_rejects_invalid_inputs(claim_text, refs):
    with pytest.raises(ValueError):
        ClaimSemanticStructuringStage().structure_claim(claim_text, refs)


def test_injected_stage_is_used_by_real_submitted_evidence_pipeline():
    adapter = StaticStructurer(_structured())
    dependencies = replace(
        OrchestrationDependencies.default(),
        claim_extractor=EvidenceClaimExtractor(adapter),
    )
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        [{"uri": SOURCE_A, "content": "Company X launched Feature A."}],
        entity="Company X",
        dependencies=dependencies,
    )
    claim = state["claims"]["claims"][0]
    assert claim["semantic_structure"]["status"] == "structured"
    assert claim["semantic_structure"]["object"] == "Feature A"
    assert claim["source_refs"] == [SOURCE_A]
    assert state["entity"]["name"] == "Company X"
    assert adapter.calls == [("Company X launched Feature A.", (SOURCE_A,))]


def test_normal_submitted_evidence_pipeline_still_abstains_by_default():
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        [{"uri": SOURCE_A, "content": "Company X launched Feature A."}],
    )
    claim = state["claims"]["claims"][0]
    assert claim["semantic_structure"]["status"] == "unstructured"
    assert claim["semantic_structure"]["reason"] == "semantic_structuring_not_attempted"
