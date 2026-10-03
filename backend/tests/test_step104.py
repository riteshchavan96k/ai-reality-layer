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


def test_usable_consumption_allows_execution():
    consumption = GroundingExecutionContextConsumptionResult.usable_result("ready")
    decision = GroundingExecutionContextConsumptionDecisionEvaluator.evaluate(consumption)
    assert decision == GroundingExecutionContextConsumptionDecisionResult.allowed_result("ready")


def test_rejected_consumption_blocks_execution():
    consumption = GroundingExecutionContextConsumptionResult.rejected_result(
        "ready", "execution_not_allowed"
    )
    decision = GroundingExecutionContextConsumptionDecisionEvaluator.evaluate(consumption)
    assert decision.status == "blocked"
    assert decision.allowed is False
    assert decision.reason == "execution_not_allowed"


def test_not_available_consumption_can_be_allowed():
    consumption = GroundingExecutionContextConsumptionResult.usable_result("not_available")
    decision = GroundingExecutionContextConsumptionDecisionEvaluator.evaluate(consumption)
    assert decision.status == "allowed"
    assert decision.grounding_status == "not_available"


def test_evaluator_rejects_wrong_input_type():
    with pytest.raises(ValueError, match="consumption must be"):
        GroundingExecutionContextConsumptionDecisionEvaluator.evaluate({})


def test_allowed_decision_cannot_have_reason():
    with pytest.raises(ValueError, match="allowed decision cannot contain a reason"):
        GroundingExecutionContextConsumptionDecision("allowed", "ready", True, "invalid")


def test_blocked_decision_requires_reason():
    with pytest.raises(ValueError, match="blocked decision requires a reason"):
        GroundingExecutionContextConsumptionDecision("blocked", "ready", False)


def test_decision_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="blocked status requires allowed=False"):
        GroundingExecutionContextConsumptionDecision("blocked", "ready", True)


def test_decision_execution_state_is_explicit():
    decision = GroundingExecutionContextConsumptionDecision(
        "allowed", "ready", True, decision_executed=False
    )
    assert decision.decision_executed is False


def test_decision_serialization_is_deterministic():
    decision = GroundingExecutionContextConsumptionDecision.allowed_result("ready")
    assert decision.to_dict() == {
        "status": "allowed",
        "grounding_status": "ready",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }
