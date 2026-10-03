import pytest

from backend.app.reality.grounding_execution_authorization import GroundingExecutionAuthorization
from backend.app.reality.grounding_execution_authorization_result import (
    GroundingExecutionAuthorizationResult,
)
from backend.app.reality.grounding_execution_authorization_evaluator import GroundingExecutionAuthorizationEvaluator
from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)


def test_allowed_decision_becomes_authorized():
    decision = GroundingExecutionContextConsumptionDecisionResult.allowed_result("ready")
    authorization = GroundingExecutionAuthorizationEvaluator.evaluate(decision)
    assert authorization == GroundingExecutionAuthorizationResult.authorized_result("ready")


def test_blocked_decision_becomes_denied():
    decision = GroundingExecutionContextConsumptionDecisionResult.blocked_result(
        "ready", "execution_context_not_prepared"
    )
    authorization = GroundingExecutionAuthorizationEvaluator.evaluate(decision)
    assert authorization.status == "denied"
    assert authorization.authorized is False
    assert authorization.reason == "execution_context_not_prepared"


def test_not_available_allowed_decision_remains_authorized():
    decision = GroundingExecutionContextConsumptionDecisionResult.allowed_result("not_available")
    authorization = GroundingExecutionAuthorizationEvaluator.evaluate(decision)
    assert authorization.grounding_status == "not_available"
    assert authorization.authorized is True


def test_evaluator_rejects_wrong_input_type():
    with pytest.raises(ValueError, match="decision_result must be"):
        GroundingExecutionAuthorizationEvaluator.evaluate({"status": "allowed"})


def test_authorized_result_cannot_have_reason():
    with pytest.raises(ValueError, match="authorized result cannot contain a reason"):
        GroundingExecutionAuthorization(
            status="authorized",
            grounding_status="ready",
            authorized=True,
            reason="unexpected",
        )


def test_denied_result_requires_reason():
    with pytest.raises(ValueError, match="denied authorization requires a reason"):
        GroundingExecutionAuthorization(
            status="denied",
            grounding_status="ready",
            authorized=False,
            reason=None,
        )


def test_invalid_authorization_state_is_rejected():
    with pytest.raises(ValueError, match="authorized status requires authorized=True"):
        GroundingExecutionAuthorization(
            status="authorized",
            grounding_status="ready",
            authorized=False,
        )


def test_invalid_grounding_status_is_rejected():
    with pytest.raises(ValueError, match="grounding_status must be"):
        GroundingExecutionAuthorization(
            status="authorized",
            grounding_status="unknown",
            authorized=True,
        )


def test_authorization_execution_state_is_preserved():
    authorization = GroundingExecutionAuthorization(
        status="denied",
        grounding_status="ready",
        authorized=False,
        reason="blocked",
        authorization_executed=False,
    )
    assert authorization.authorization_executed is False


def test_decision_execution_state_flows_into_authorization():
    decision = GroundingExecutionContextConsumptionDecisionResult(
        status="blocked",
        grounding_status="ready",
        allowed=False,
        reason="blocked",
        decision_executed=False,
    )
    authorization = GroundingExecutionAuthorizationEvaluator.evaluate(decision)
    assert authorization.authorization_executed is False


def test_serialization_is_deterministic():
    authorization = GroundingExecutionAuthorization.denied_result(
        "ready", "execution_context_not_prepared"
    )
    assert authorization.to_dict() == {
        "status": "denied",
        "grounding_status": "ready",
        "authorized": False,
        "reason": "execution_context_not_prepared",
        "authorization_executed": True,
    }
