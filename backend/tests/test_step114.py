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


def test_evaluator_returns_canonical_decision_result():
    consumption = GroundingExecutionAuthorizationConsumptionResult.usable_result(
        "authorized"
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionEvaluator.evaluate(consumption)
    assert isinstance(result, GroundingExecutionAuthorizationConsumptionDecisionResult)
    assert result.status == "allowed"
    assert result.authorization_status == "authorized"
    assert result.allowed is True


def test_result_preserves_blocked_reason():
    consumption = GroundingExecutionAuthorizationConsumptionResult.rejected_result(
        "denied", "authorization_denied"
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionEvaluator.evaluate(consumption)
    assert result.status == "blocked"
    assert result.authorization_status == "denied"
    assert result.allowed is False
    assert result.reason == "authorization_denied"


def test_result_preserves_authorization_status():
    consumption = GroundingExecutionAuthorizationConsumptionResult.usable_result(
        "authorized"
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionEvaluator.evaluate(consumption)
    assert result.authorization_status == "authorized"
    assert result.allowed is True


def test_result_from_decision_requires_canonical_decision():
    with pytest.raises(ValueError, match="decision must be"):
        GroundingExecutionAuthorizationConsumptionDecisionResult.from_decision({})


def test_allowed_result_cannot_have_reason():
    with pytest.raises(ValueError, match="allowed decision cannot contain a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResult(
            "allowed", "authorized", True, "invalid"
        )


def test_blocked_result_requires_reason():
    with pytest.raises(ValueError, match="blocked decision requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResult(
            "blocked", "denied", False
        )


def test_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="allowed status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResult(
            "allowed", "authorized", False
        )


def test_authorization_status_must_match_allowed_state():
    with pytest.raises(ValueError, match="authorized status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResult(
            "blocked", "authorized", False, "blocked"
        )
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResult(
            "allowed", "denied", True
        )


def test_decision_execution_state_is_preserved():
    decision = GroundingExecutionAuthorizationConsumptionDecision(
        "allowed", "authorized", True, decision_executed=False
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionResult.from_decision(decision)
    assert result.decision_executed is False


def test_result_serialization_is_deterministic():
    result = GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result(
        "authorized"
    )
    assert result.to_dict() == {
        "status": "allowed",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }
