import pytest

from backend.app.reality.grounding_execution_context_consumption_decision import (
    GroundingExecutionContextConsumptionDecision,
)
from backend.app.reality.grounding_execution_context_consumption_decision_evaluator import (
    GroundingExecutionContextConsumptionDecisionEvaluator,
)
from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


def test_evaluator_returns_canonical_decision_result():
    consumption = GroundingExecutionContextConsumptionResult.usable_result("ready")
    result = GroundingExecutionContextConsumptionDecisionEvaluator.evaluate(consumption)
    assert isinstance(result, GroundingExecutionContextConsumptionDecisionResult)
    assert result.status == "allowed"
    assert result.allowed is True


def test_result_preserves_blocked_reason():
    consumption = GroundingExecutionContextConsumptionResult.rejected_result(
        "ready", "execution_not_allowed"
    )
    result = GroundingExecutionContextConsumptionDecisionEvaluator.evaluate(consumption)
    assert result.status == "blocked"
    assert result.allowed is False
    assert result.reason == "execution_not_allowed"


def test_result_preserves_not_available_grounding_status():
    consumption = GroundingExecutionContextConsumptionResult.usable_result("not_available")
    result = GroundingExecutionContextConsumptionDecisionEvaluator.evaluate(consumption)
    assert result.grounding_status == "not_available"
    assert result.allowed is True


def test_result_from_decision_requires_canonical_decision():
    with pytest.raises(ValueError, match="decision must be"):
        GroundingExecutionContextConsumptionDecisionResult.from_decision({})


def test_allowed_result_cannot_have_reason():
    with pytest.raises(ValueError, match="allowed decision cannot contain a reason"):
        GroundingExecutionContextConsumptionDecisionResult(
            "allowed", "ready", True, "invalid"
        )


def test_blocked_result_requires_reason():
    with pytest.raises(ValueError, match="blocked decision requires a reason"):
        GroundingExecutionContextConsumptionDecisionResult("blocked", "ready", False)


def test_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="allowed status requires allowed=True"):
        GroundingExecutionContextConsumptionDecisionResult("allowed", "ready", False)


def test_invalid_grounding_status_is_rejected():
    with pytest.raises(ValueError, match="grounding_status must be"):
        GroundingExecutionContextConsumptionDecisionResult("allowed", "invalid", True)


def test_decision_execution_state_is_preserved():
    decision = GroundingExecutionContextConsumptionDecision(
        "allowed", "ready", True, decision_executed=False
    )
    result = GroundingExecutionContextConsumptionDecisionResult.from_decision(decision)
    assert result.decision_executed is False


def test_result_serialization_is_deterministic():
    result = GroundingExecutionContextConsumptionDecisionResult.allowed_result("ready")
    assert result.to_dict() == {
        "status": "allowed",
        "grounding_status": "ready",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }
