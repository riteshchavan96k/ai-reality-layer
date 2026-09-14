import pytest

from backend.app.reality.grounding_execution_gate import GroundingExecutionGateResult
from backend.app.reality.grounding_execution_gate_normalizer import GroundingExecutionGateResultNormalizer


def test_typed_gate_result_is_preserved() -> None:
    result = GroundingExecutionGateResult.allowed_result("ready")
    normalized = GroundingExecutionGateResultNormalizer.normalize(result)
    assert normalized is result


def test_allowed_mapping_is_normalized() -> None:
    normalized = GroundingExecutionGateResultNormalizer.normalize(
        {"status": "allowed", "grounding_status": "ready", "allowed": True}
    )
    assert normalized.to_dict() == {
        "status": "allowed",
        "grounding_status": "ready",
        "allowed": True,
        "reason": None,
        "gate_evaluated": True,
    }


def test_blocked_mapping_preserves_reason() -> None:
    normalized = GroundingExecutionGateResultNormalizer.normalize(
        {
            "status": "blocked",
            "grounding_status": "ready",
            "allowed": False,
            "reason": "empty_grounding_context",
        }
    )
    assert normalized.reason == "empty_grounding_context"


def test_not_available_mapping_is_normalized() -> None:
    normalized = GroundingExecutionGateResultNormalizer.normalize(
        {"status": "allowed", "grounding_status": "not_available", "allowed": True}
    )
    assert normalized.grounding_status == "not_available"


def test_explicit_gate_evaluation_state_is_preserved() -> None:
    normalized = GroundingExecutionGateResultNormalizer.normalize(
        {
            "status": "blocked",
            "grounding_status": "ready",
            "allowed": False,
            "reason": "grounding_context_rejected",
            "gate_evaluated": False,
        }
    )
    assert normalized.gate_evaluated is False


def test_unsupported_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingExecutionGateResultNormalizer.normalize("invalid")


def test_invalid_mapping_is_rejected_by_canonical_contract() -> None:
    with pytest.raises(ValueError, match="allowed status requires allowed=True"):
        GroundingExecutionGateResultNormalizer.normalize(
            {"status": "allowed", "grounding_status": "ready", "allowed": False}
        )


def test_invalid_grounding_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="grounding_status must be ready or not_available"):
        GroundingExecutionGateResultNormalizer.normalize(
            {"status": "allowed", "grounding_status": "unknown", "allowed": True}
        )


def test_serialization_remains_deterministic_after_normalization() -> None:
    normalized = GroundingExecutionGateResultNormalizer.normalize(
        {
            "status": "blocked",
            "grounding_status": "ready",
            "allowed": False,
            "reason": "empty_grounding_context",
        }
    )
    assert normalized.to_dict() == {
        "status": "blocked",
        "grounding_status": "ready",
        "allowed": False,
        "reason": "empty_grounding_context",
        "gate_evaluated": True,
    }
