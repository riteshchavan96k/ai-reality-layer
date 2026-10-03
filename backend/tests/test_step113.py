import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision import (
    GroundingExecutionAuthorizationConsumptionDecision,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_evaluator import (
    GroundingExecutionAuthorizationConsumptionDecisionEvaluator,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)


def test_usable_authorization_consumption_allows_execution():
    consumption = GroundingExecutionAuthorizationConsumptionResult.usable_result()
    decision = GroundingExecutionAuthorizationConsumptionDecisionEvaluator.evaluate(consumption)
    assert decision == GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result(
        "authorized"
    )


def test_rejected_authorization_consumption_blocks_execution():
    consumption = GroundingExecutionAuthorizationConsumptionResult.rejected_result(
        "denied", "execution_authorization_denied"
    )
    decision = GroundingExecutionAuthorizationConsumptionDecisionEvaluator.evaluate(consumption)
    assert decision.status == "blocked"
    assert decision.allowed is False
    assert decision.authorization_status == "denied"
    assert decision.reason == "execution_authorization_denied"


def test_evaluator_preserves_authorization_status():
    consumption = GroundingExecutionAuthorizationConsumptionResult.rejected_result(
        "denied", "authorization_policy_rejected"
    )
    decision = GroundingExecutionAuthorizationConsumptionDecisionEvaluator.evaluate(consumption)
    assert decision.authorization_status == "denied"
    assert decision.reason == "authorization_policy_rejected"


def test_evaluator_rejects_wrong_input_type():
    with pytest.raises(ValueError, match="consumption must be"):
        GroundingExecutionAuthorizationConsumptionDecisionEvaluator.evaluate({})


def test_allowed_decision_cannot_have_reason():
    with pytest.raises(ValueError, match="allowed decision cannot contain a reason"):
        GroundingExecutionAuthorizationConsumptionDecision(
            "allowed", "authorized", True, "unexpected"
        )


def test_blocked_decision_requires_reason():
    with pytest.raises(ValueError, match="blocked decision requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecision("blocked", "denied", False)


def test_decision_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="blocked status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecision("blocked", "denied", True)


def test_authorization_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecision("allowed", "denied", True)


def test_authorization_status_must_match_blocked_state():
    with pytest.raises(ValueError, match="authorized status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecision("blocked", "authorized", False, "blocked")


def test_decision_execution_state_is_explicit():
    decision = GroundingExecutionAuthorizationConsumptionDecision(
        "allowed", "authorized", True, decision_executed=False
    )
    assert decision.decision_executed is False


def test_decision_serialization_is_deterministic():
    decision = GroundingExecutionAuthorizationConsumptionDecision.allowed_result()
    assert decision.to_dict() == {
        "status": "allowed",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }
