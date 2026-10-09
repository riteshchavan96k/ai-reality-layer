"""Step 210 — bounded optional semantic structuring input, no silent truncation."""

from dataclasses import replace

import pytest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.claim_semantic_structure import ClaimSemanticStructure
from backend.app.reality.claim_semantic_structurer import (
    ClaimSemanticStructuringStage,
    MAX_CLAIM_SEMANTIC_INPUT_CHARS,
)
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


SOURCE_A = "https://example.test/a"
SOURCE_B = "https://example.test/b"


class RecordingStructurer:
    def __init__(self):
        self.calls = []

    def structure(self, text, source_refs):
        self.calls.append((text, source_refs))
        return ClaimSemanticStructure.structured(
            subject="Company X", predicate="launched", object="Feature A",
            structuring_method="test_adapter",
        )


def _long_claim(extra=1):
    # One sentence, not multiple short claims; within the 50k document limit.
    return "A" * (MAX_CLAIM_SEMANTIC_INPUT_CHARS - 1 + extra) + "."


def test_length_policy_is_deterministic():
    assert MAX_CLAIM_SEMANTIC_INPUT_CHARS == 10_000
    assert len(_long_claim(0)) == MAX_CLAIM_SEMANTIC_INPUT_CHARS
    assert len(_long_claim(1)) == MAX_CLAIM_SEMANTIC_INPUT_CHARS + 1


def test_configured_adapter_accepts_claim_at_exact_input_limit():
    adapter = RecordingStructurer()
    text = _long_claim(0)
    semantic = ClaimSemanticStructuringStage(adapter).structure_claim(
        text, (SOURCE_A,)
    )
    assert semantic.status == "structured"
    assert adapter.calls == [(text, (SOURCE_A,))]


def test_configured_adapter_skips_one_char_over_limit_before_invocation():
    adapter = RecordingStructurer()
    text = _long_claim(1)
    semantic = ClaimSemanticStructuringStage(adapter).structure_claim(
        text, (SOURCE_A,)
    )
    assert semantic.status == "unstructured"
    assert semantic.reason == "semantic_structuring_input_too_long"
    assert adapter.calls == []


def test_no_adapter_preserves_step207_no_attempt_default_for_long_text():
    text = _long_claim(1)
    semantic = ClaimSemanticStructuringStage().structure_claim(
        text, (SOURCE_A,)
    )
    assert semantic == ClaimSemanticStructure.unstructured()


def test_long_claim_is_not_truncated_or_removed_by_extraction():
    adapter = RecordingStructurer()
    text = _long_claim(1)
    result = EvidenceClaimExtractor(adapter).extract_result({
        "status": "completed",
        "sources": [{"uri": SOURCE_A, "content": text}],
        "content": text,
    })
    assert result.status == "usable"
    assert len(result.claims) == 1
    assert result.claims[0].text == text
    assert len(result.claims[0].text) == MAX_CLAIM_SEMANTIC_INPUT_CHARS + 1
    assert result.claims[0].source_refs == (SOURCE_A,)
    assert result.claims[0].semantic_structure.reason == (
        "semantic_structuring_input_too_long"
    )
    assert adapter.calls == []


def test_long_claim_is_skipped_but_short_claim_is_still_structured():
    adapter = RecordingStructurer()
    long_text = _long_claim(1)
    short_text = "Company X launched Feature A."
    content = long_text + " " + short_text
    result = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable", "sources": [{"uri": SOURCE_A}],
        "content": content,
    })
    assert result.status == "usable"
    assert [claim.text for claim in result.claims] == [long_text, short_text]
    assert result.claims[0].semantic_structure.reason == (
        "semantic_structuring_input_too_long"
    )
    assert result.claims[1].semantic_structure.status == "structured"
    assert adapter.calls == [(short_text, (SOURCE_A,))]


def test_submitted_cross_source_duplicate_long_claim_preserves_all_refs():
    adapter = RecordingStructurer()
    long_text = _long_claim(1)
    bundle = SubmittedEvidenceBundle.from_mappings([
        {"uri": SOURCE_A, "content": long_text},
        {"uri": SOURCE_B, "content": long_text},
    ])
    result = bundle.extract_claims(EvidenceClaimExtractor(adapter))
    assert result.status == "usable"
    assert len(result.claims) == 1
    claim = result.claims[0]
    assert claim.text == long_text
    assert claim.source_refs == (SOURCE_A, SOURCE_B)
    assert claim.semantic_structure.reason == "semantic_structuring_input_too_long"
    assert adapter.calls == []


def test_submitted_multi_source_mixed_claims_only_invoke_short_unique_claim():
    adapter = RecordingStructurer()
    long_text = _long_claim(1)
    short_text = "Company X launched Feature A."
    bundle = SubmittedEvidenceBundle.from_mappings([
        {"uri": SOURCE_A, "content": long_text + " " + short_text},
        {"uri": SOURCE_B, "content": long_text + " " + short_text},
    ])
    result = bundle.extract_claims(EvidenceClaimExtractor(adapter))
    assert [claim.text for claim in result.claims] == [long_text, short_text]
    assert all(claim.source_refs == (SOURCE_A, SOURCE_B) for claim in result.claims)
    assert result.claims[0].semantic_structure.reason == (
        "semantic_structuring_input_too_long"
    )
    assert result.claims[1].semantic_structure.status == "structured"
    assert adapter.calls == [(short_text, (SOURCE_A, SOURCE_B))]


@pytest.mark.parametrize("ref", [(), ("",), ["https://example.test/a"]])
def test_existing_reference_validation_still_runs_before_size_gate(ref):
    with pytest.raises(ValueError, match="valid source references"):
        ClaimSemanticStructuringStage(RecordingStructurer()).structure_claim(
            _long_claim(1), ref
        )


def test_submitted_reality_state_retains_long_claim_and_source_lineage():
    adapter = RecordingStructurer()
    long_text = _long_claim(1)
    dependencies = replace(
        OrchestrationDependencies.default(),
        claim_extractor=EvidenceClaimExtractor(adapter),
    )
    state = build_reality_state_from_evidence(
        "What is the status of Company X?",
        [{"uri": SOURCE_A, "content": long_text},
         {"uri": SOURCE_B, "content": long_text}],
        entity="Company X",
        dependencies=dependencies,
    )
    claim = state["claims"]["claims"][0]
    assert claim["text"] == long_text
    assert claim["source_refs"] == [SOURCE_A, SOURCE_B]
    assert claim["semantic_structure"]["status"] == "unstructured"
    assert claim["semantic_structure"]["reason"] == (
        "semantic_structuring_input_too_long"
    )
    assert state["entity"]["name"] == "Company X"
    assert adapter.calls == []


def test_no_model_submitted_state_remains_not_attempted_even_for_long_claim():
    long_text = _long_claim(1)
    state = build_reality_state_from_evidence(
        "What is the status of Company X?",
        [{"uri": SOURCE_A, "content": long_text}],
    )
    claim = state["claims"]["claims"][0]
    assert claim["text"] == long_text
    assert claim["semantic_structure"]["reason"] == (
        "semantic_structuring_not_attempted"
    )


def test_normal_length_submitted_state_uses_injected_adapter():
    adapter = RecordingStructurer()
    dependencies = replace(
        OrchestrationDependencies.default(),
        claim_extractor=EvidenceClaimExtractor(adapter),
    )
    text = "Company X launched Feature A."
    state = build_reality_state_from_evidence(
        "What did Company X launch?",
        [{"uri": SOURCE_A, "content": text}],
        dependencies=dependencies,
    )
    claim = state["claims"]["claims"][0]
    assert claim["semantic_structure"]["status"] == "structured"
    assert claim["source_refs"] == [SOURCE_A]
    assert adapter.calls == [(text, (SOURCE_A,))]
