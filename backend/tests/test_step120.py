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


def test_allowed_decision_produces_canonical_result():
    consumption_result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult.usable_result()
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator.evaluate(consumption_result)
    assert result == GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result(
        "authorized"
    )


def test_blocked_decision_produces_result_and_preserves_reason():
    consumption_result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult.rejected_result(
        "denied", "authorization_decision_rejected"
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator.evaluate(consumption_result)
    assert result.status == "blocked"
    assert result.allowed is False
    assert result.authorization_status == "denied"
    assert result.reason == "authorization_decision_rejected"
    assert result.decision_executed is True


def test_result_rejects_wrong_status():
    with pytest.raises(ValueError, match="status must be allowed or blocked"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
            "invalid", "authorized", True
        )


def test_result_rejects_allowed_status_with_false_allowed():
    with pytest.raises(ValueError, match="allowed status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
            "allowed", "authorized", False
        )


def test_result_rejects_blocked_status_with_true_allowed():
    with pytest.raises(ValueError, match="blocked status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
            "blocked", "denied", True
        )


def test_result_rejects_reason_on_allowed_result():
    with pytest.raises(ValueError, match="allowed decision result cannot contain a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
            "allowed", "authorized", True, "unexpected"
        )


def test_result_requires_reason_on_blocked_result():
    with pytest.raises(ValueError, match="blocked decision result requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
            "blocked", "denied", False
        )


def test_result_rejects_authorized_blocked_state():
    with pytest.raises(ValueError, match="authorized status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
            "blocked", "authorized", False, "rejected"
        )


def test_result_rejects_denied_allowed_state():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
            "allowed", "denied", True
        )


def test_from_decision_requires_canonical_decision():
    with pytest.raises(ValueError, match="decision must be"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.from_decision({})


def test_result_serialization_is_deterministic():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result()
    assert result.to_dict() == {
        "status": "allowed",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }
