import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_evaluator import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator,
)


def test_usable_consumption_result_allows_execution():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult.usable_result()
    decision_result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator.evaluate(result)
    assert decision_result == GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result("authorized")


def test_rejected_consumption_result_blocks_execution_and_preserves_reason():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult.rejected_result(
        "denied", "authorization_decision_rejected"
    )
    decision_result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator.evaluate(result)
    assert decision_result.status == "blocked"
    assert decision_result.allowed is False
    assert decision_result.authorization_status == "denied"
    assert decision_result.reason == "authorization_decision_rejected"


def test_evaluator_rejects_wrong_input_type():
    with pytest.raises(ValueError, match="consumption_result must be"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator.evaluate({})


def test_evaluator_rejects_unexecuted_decision_result_consumption():
    with pytest.raises(ValueError, match="decision_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "authorized", True, decision_executed=False
        )


def test_evaluator_rejects_unexecuted_consumption():
    with pytest.raises(ValueError, match="consumption_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "authorized", True, consumption_executed=False
        )


def test_allowed_decision_cannot_have_reason():
    with pytest.raises(ValueError, match="allowed decision cannot contain a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision(
            "allowed", "authorized", True, "unexpected"
        )


def test_blocked_decision_requires_reason():
    with pytest.raises(ValueError, match="blocked decision requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision(
            "blocked", "denied", False
        )


def test_decision_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="blocked status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision(
            "blocked", "denied", True
        )


def test_authorization_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision(
            "allowed", "denied", True
        )


def test_decision_serialization_is_deterministic():
    decision = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision.allowed_result()
    decision_result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.from_decision(decision)
    assert decision_result.to_dict() == {
        "status": "allowed",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }
