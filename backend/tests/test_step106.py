import pytest

from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_context_consumption_decision_result_normalizer import (
    GroundingExecutionContextConsumptionDecisionResultNormalizer,
)


def test_typed_result_is_preserved():
    result = GroundingExecutionContextConsumptionDecisionResult.allowed_result("ready")
    assert GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(result) is result


def test_allowed_mapping_is_normalized():
    result = GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
        {"status": "allowed", "grounding_status": "ready", "allowed": True}
    )
    assert isinstance(result, GroundingExecutionContextConsumptionDecisionResult)
    assert result.to_dict() == {
        "status": "allowed",
        "grounding_status": "ready",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }


def test_blocked_mapping_preserves_reason():
    result = GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
        {
            "status": "blocked",
            "grounding_status": "ready",
            "allowed": False,
            "reason": "execution_not_allowed",
        }
    )
    assert result.reason == "execution_not_allowed"


def test_not_available_mapping_is_supported():
    result = GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
        {"status": "allowed", "grounding_status": "not_available", "allowed": True}
    )
    assert result.grounding_status == "not_available"
    assert result.allowed is True


def test_explicit_decision_state_is_preserved():
    result = GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
        {
            "status": "allowed",
            "grounding_status": "ready",
            "allowed": True,
            "decision_executed": False,
        }
    )
    assert result.decision_executed is False


def test_invalid_mapping_is_rejected_by_contract():
    with pytest.raises(ValueError, match="allowed status requires allowed=True"):
        GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
            {"status": "allowed", "grounding_status": "ready", "allowed": False}
        )


def test_non_mapping_is_rejected():
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(object())


def test_invalid_grounding_status_is_rejected():
    with pytest.raises(ValueError, match="grounding_status must be"):
        GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
            {"status": "allowed", "grounding_status": "invalid", "allowed": True}
        )


def test_blocked_mapping_requires_reason():
    with pytest.raises(ValueError, match="blocked decision requires a reason"):
        GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
            {"status": "blocked", "grounding_status": "ready", "allowed": False}
        )


def test_serialization_is_deterministic():
    result = GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(
        {"status": "allowed", "grounding_status": "ready", "allowed": True}
    )
    assert result.to_dict() == GroundingExecutionContextConsumptionDecisionResult.allowed_result("ready").to_dict()
