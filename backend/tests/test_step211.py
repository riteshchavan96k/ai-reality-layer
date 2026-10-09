"""Step 211: bound optional semantic-adapter invocations for usable evidence.

Step 184 intentionally preserved the lower-level usable/no-adapter legacy
contract. New opt-in semantic inference must still fail closed at the shared
2,000-unique-claim resource limit before it calls an adapter.
"""

from dataclasses import replace

import pytest

from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.claim_conflict_detector import ClaimConflictDetector
from backend.app.reality.claim_evidence_linker import ClaimEvidenceLinker
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.claim_semantic_structure import ClaimSemanticStructure
from backend.app.reality.retrieval_input_bounds import MAX_RETRIEVED_CLAIMS
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle

A = "https://example.test/a"
B = "https://example.test/b"


class RecordingStructurer:
    def __init__(self):
        self.calls = []

    def structure(self, claim_text, source_refs):
        self.calls.append((claim_text, source_refs))
        return ClaimSemanticStructure.unstructured("semantic_model_abstained")


def _sentences(start, count):
    return " ".join(f"Fact {i}." for i in range(start, start + count))


def _evidence(status, content):
    return {"status": status, "content": content, "sources": [{"uri": A}]}


@pytest.mark.parametrize("status", ["completed", "usable"])
def test_optional_semantic_adapter_never_runs_for_overbudget_claims(status):
    adapter = RecordingStructurer()
    result = EvidenceClaimExtractor(adapter).extract_result(
        _evidence(status, _sentences(0, MAX_RETRIEVED_CLAIMS + 1))
    )
    assert result.status == "unavailable"
    assert result.reason == "retrieved_claim_limit_exceeded"
    assert result.claims == ()
    assert result.source_count == 1
    assert adapter.calls == []


def test_usable_legacy_no_adapter_behavior_remains_explicitly_supported():
    result = EvidenceClaimExtractor().extract_result(
        _evidence("usable", _sentences(0, MAX_RETRIEVED_CLAIMS + 1))
    )
    assert result.status == "usable"
    assert len(result.claims) == MAX_RETRIEVED_CLAIMS + 1


def test_usable_configured_adapter_runs_at_exact_budget():
    adapter = RecordingStructurer()
    result = EvidenceClaimExtractor(adapter).extract_result(
        _evidence("usable", _sentences(0, MAX_RETRIEVED_CLAIMS))
    )
    assert result.status == "usable"
    assert len(result.claims) == MAX_RETRIEVED_CLAIMS
    assert len(adapter.calls) == MAX_RETRIEVED_CLAIMS
    assert adapter.calls[0] == ("Fact 0.", (A,))
    assert adapter.calls[-1] == (
        f"Fact {MAX_RETRIEVED_CLAIMS - 1}.", (A,)
    )
    assert result.claims[0].semantic_structure.reason == "semantic_model_abstained"


def test_usable_multi_source_overbudget_does_not_call_adapter():
    adapter = RecordingStructurer()
    first = _sentences(0, 1000)
    second = _sentences(1000, MAX_RETRIEVED_CLAIMS - 999)
    result = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable",
        "sources": [
            {"uri": A, "content": first},
            {"uri": B, "content": second},
        ],
        "content": first + "\n\n" + second,
    })
    assert result.status == "unavailable"
    assert result.reason == "retrieved_claim_limit_exceeded"
    assert result.source_count == 2
    assert result.claims == ()
    assert adapter.calls == []


def test_usable_cross_source_duplicates_do_not_count_twice():
    adapter = RecordingStructurer()
    content = _sentences(0, MAX_RETRIEVED_CLAIMS)
    result = EvidenceClaimExtractor(adapter).extract_result({
        "status": "usable",
        "sources": [
            {"uri": A, "content": content},
            {"uri": B, "content": content},
        ],
        "content": content + "\n\n" + content,
    })
    assert result.status == "usable"
    assert result.source_count == 2
    assert len(result.claims) == MAX_RETRIEVED_CLAIMS
    assert len(adapter.calls) == MAX_RETRIEVED_CLAIMS
    assert adapter.calls[0] == ("Fact 0.", (A, B))
    assert adapter.calls[-1] == (
        f"Fact {MAX_RETRIEVED_CLAIMS - 1}.", (A, B)
    )


def test_rejected_usable_claim_graph_cannot_be_linked_or_conflicted():
    adapter = RecordingStructurer()
    evidence = _evidence("usable", _sentences(0, MAX_RETRIEVED_CLAIMS + 1))
    result = EvidenceClaimExtractor(adapter).extract_result(evidence)
    linking = ClaimEvidenceLinker().link_result(result, evidence)
    conflicts = ClaimConflictDetector().detect_result(result)
    assert linking.status == "unavailable"
    assert linking.links == ()
    assert conflicts.status == "unavailable"
    assert conflicts.conflicts == ()
    assert adapter.calls == []


def test_submitted_evidence_keeps_existing_error_translation_with_adapter():
    adapter = RecordingStructurer()
    bundle = SubmittedEvidenceBundle.from_mappings([
        {"uri": A, "content": _sentences(0, 1200)},
        {"uri": B, "content": _sentences(1200, 801)},
    ])
    result = bundle.extract_claims(EvidenceClaimExtractor(adapter))
    assert result.status == "unavailable"
    assert result.reason == "submitted_claim_limit_exceeded"
    assert result.claims == ()
    assert result.source_count == 2
    assert adapter.calls == []


def test_full_submitted_reality_state_does_not_create_partial_claim_links():
    adapter = RecordingStructurer()
    deps = replace(
        OrchestrationDependencies.default(),
        claim_extractor=EvidenceClaimExtractor(adapter),
    )
    state = build_reality_state_from_evidence(
        "What are the current facts about Company X?",
        [
            {"uri": A, "content": _sentences(0, 1200)},
            {"uri": B, "content": _sentences(1200, 801)},
        ],
        dependencies=deps,
    )
    assert state["claims"]["status"] == "unavailable"
    assert state["claims"]["reason"] == "submitted_claim_limit_exceeded"
    assert state["claims"]["claim_count"] == 0
    assert state["claim_evidence_linking"]["links"] == []
    assert state["status"] != "supported"
    assert adapter.calls == []


def test_normal_usable_claim_still_preserves_source_refs_and_semantics():
    adapter = RecordingStructurer()
    evidence = _evidence("usable", "Company X launched Feature A.")
    result = EvidenceClaimExtractor(adapter).extract_result(evidence)
    assert result.status == "usable"
    assert result.claims[0].text == "Company X launched Feature A."
    assert result.claims[0].source_refs == (A,)
    assert result.claims[0].semantic_structure.reason == "semantic_model_abstained"
    assert adapter.calls == [("Company X launched Feature A.", (A,))]
