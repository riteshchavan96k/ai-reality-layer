import pytest

from backend.app.reality.reality_state import RealityState
from backend.app.reality.reality_state_builder import RealityStateBuilder
from backend.app.reality.reality_state_normalizer import RealityStateNormalizer


def base_state():
    return {
        "status": "supported",
        "task": "Verify the evidence-backed answer.",
        "evidence": {"status": "usable"},
        "claims": {"status": "usable", "claim_count": 1},
        "claim_evidence_linking": {"status": "usable", "claim_count": 1, "linked_claim_count": 1},
        "source_provenance": {"status": "usable"},
        "source_observation": {"status": "usable"},
        "freshness": {"status": "usable"},
        "conflicts": {"status": "empty", "conflict_count": 0},
        "confidence_signals": {"status": "supported"},
        "assembly_method": "deterministic_signal_snapshot",
        "reason": None,
    }


def test_step161_accepts_canonical_reality_state():
    result = RealityState.validate(base_state())
    assert isinstance(result, RealityState)
    assert result.status == "supported"


def test_step161_normalizes_mapping():
    result = RealityStateNormalizer.normalize(base_state())
    assert isinstance(result, RealityState)
    assert result.task == "Verify the evidence-backed answer."


def test_step161_rejects_missing_required_field():
    raw = base_state()
    del raw["confidence_signals"]
    with pytest.raises(ValueError, match="missing required fields"):
        RealityState.validate(raw)


def test_step161_rejects_invalid_snapshot_shape():
    raw = base_state()
    raw["freshness"] = []
    with pytest.raises(ValueError, match="freshness must be a dictionary"):
        RealityStateNormalizer.normalize(raw)


def test_step161_rejects_unavailable_without_reason():
    raw = base_state()
    raw["status"] = "unavailable"
    with pytest.raises(ValueError, match="unavailable state requires a reason"):
        RealityState.validate(raw)


def test_step161_builder_returns_canonical_validated_result():
    result = RealityStateBuilder().build_result(
        base_state()["task"],
        base_state()["evidence"],
        base_state()["claims"],
        base_state()["claim_evidence_linking"],
        base_state()["source_provenance"],
        base_state()["source_observation"],
        base_state()["freshness"],
        base_state()["conflicts"],
        base_state()["confidence_signals"],
    )
    assert isinstance(result, RealityState)
    assert result.status == "supported"
    assert result.assembly_method == "deterministic_signal_snapshot"
