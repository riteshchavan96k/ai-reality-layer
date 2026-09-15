from backend.app.reality.grounding_execution_authorization import GroundingExecutionAuthorization
from backend.app.reality.grounding_execution_authorization_evaluator import GroundingExecutionAuthorizationEvaluator
from backend.app.reality.grounding_execution_authorization_result import GroundingExecutionAuthorizationResult
from backend.app.reality.grounding_execution_context_consumption_decision_result import GroundingExecutionContextConsumptionDecisionResult


def test_evaluator_returns_canonical_authorization_result_for_allowed_decision() -> None:
    decision = GroundingExecutionContextConsumptionDecisionResult("allowed", "ready", True)
    result = GroundingExecutionAuthorizationEvaluator.evaluate(decision)
    assert isinstance(result, GroundingExecutionAuthorizationResult)
    assert result.to_dict() == {
        "status": "authorized", "grounding_status": "ready", "authorized": True,
        "reason": None, "authorization_executed": True,
    }


def test_evaluator_returns_denied_result_and_preserves_reason() -> None:
    decision = GroundingExecutionContextConsumptionDecisionResult(
        "blocked", "ready", False, "execution_context_not_prepared"
    )
    result = GroundingExecutionAuthorizationEvaluator.evaluate(decision)
    assert result.status == "denied"
    assert result.authorized is False
    assert result.reason == "execution_context_not_prepared"


def test_authorization_result_preserves_not_available_grounding_state() -> None:
    result = GroundingExecutionAuthorizationEvaluator.evaluate(
        GroundingExecutionContextConsumptionDecisionResult("allowed", "not_available", True)
    )
    assert result.grounding_status == "not_available"
    assert result.authorized is True


def test_authorization_result_preserves_execution_state() -> None:
    result = GroundingExecutionAuthorizationEvaluator.evaluate(
        GroundingExecutionContextConsumptionDecisionResult("allowed", "ready", True, decision_executed=False)
    )
    assert result.authorization_executed is False


def test_invalid_evaluator_input_is_rejected() -> None:
    try:
        GroundingExecutionAuthorizationEvaluator.evaluate(object())
    except ValueError as exc:
        assert "decision_result" in str(exc)
    else:
        raise AssertionError("invalid decision input should be rejected")


def test_authorized_result_cannot_have_reason() -> None:
    try:
        GroundingExecutionAuthorizationResult("authorized", "ready", True, "unexpected")
    except ValueError as exc:
        assert "reason" in str(exc)
    else:
        raise AssertionError("authorized result with reason should be rejected")


def test_denied_result_requires_reason() -> None:
    try:
        GroundingExecutionAuthorizationResult("denied", "ready", False)
    except ValueError as exc:
        assert "reason" in str(exc)
    else:
        raise AssertionError("denied result without reason should be rejected")


def test_authorization_contract_can_be_converted_to_result() -> None:
    authorization = GroundingExecutionAuthorization.denied_result("ready", "execution_authorization_denied")
    result = GroundingExecutionAuthorizationResult.from_authorization(authorization)
    assert result.to_dict() == authorization.to_dict()


def test_invalid_grounding_status_is_rejected() -> None:
    try:
        GroundingExecutionAuthorizationResult("authorized", "invalid", True)
    except ValueError as exc:
        assert "grounding_status" in str(exc)
    else:
        raise AssertionError("invalid grounding status should be rejected")


def test_serialization_is_deterministic() -> None:
    result = GroundingExecutionAuthorizationResult.authorized_result("ready")
    assert result.to_dict() == {
        "status": "authorized", "grounding_status": "ready", "authorized": True,
        "reason": None, "authorization_executed": True,
    }
