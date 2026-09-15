from backend.app.reality.grounding_execution_authorization import GroundingExecutionAuthorization
from backend.app.reality.grounding_execution_authorization_evaluator import GroundingExecutionAuthorizationEvaluator
from backend.app.reality.grounding_execution_authorization_result import GroundingExecutionAuthorizationResult
from backend.app.reality.grounding_execution_authorization_result_normalizer import GroundingExecutionAuthorizationResultNormalizer
from backend.app.reality.grounding_execution_context_consumption_decision_result import GroundingExecutionContextConsumptionDecisionResult


def test_typed_result_is_preserved() -> None:
    result = GroundingExecutionAuthorizationResult.authorized_result("ready")
    normalized = GroundingExecutionAuthorizationResultNormalizer.normalize(result)
    assert normalized is result


def test_authorized_mapping_is_normalized() -> None:
    normalized = GroundingExecutionAuthorizationResultNormalizer.normalize(
        {"status": "authorized", "grounding_status": "ready", "authorized": True}
    )
    assert isinstance(normalized, GroundingExecutionAuthorizationResult)
    assert normalized.authorized is True
    assert normalized.reason is None


def test_denied_mapping_preserves_reason() -> None:
    normalized = GroundingExecutionAuthorizationResultNormalizer.normalize(
        {
            "status": "denied",
            "grounding_status": "ready",
            "authorized": False,
            "reason": "execution_context_not_prepared",
        }
    )
    assert normalized.reason == "execution_context_not_prepared"


def test_not_available_mapping_is_normalized() -> None:
    normalized = GroundingExecutionAuthorizationResultNormalizer.normalize(
        {"status": "authorized", "grounding_status": "not_available", "authorized": True}
    )
    assert normalized.grounding_status == "not_available"


def test_default_execution_state_is_true() -> None:
    normalized = GroundingExecutionAuthorizationResultNormalizer.normalize(
        {"status": "authorized", "grounding_status": "ready", "authorized": True}
    )
    assert normalized.authorization_executed is True


def test_explicit_execution_state_is_preserved() -> None:
    normalized = GroundingExecutionAuthorizationResultNormalizer.normalize(
        {
            "status": "authorized",
            "grounding_status": "ready",
            "authorized": True,
            "authorization_executed": False,
        }
    )
    assert normalized.authorization_executed is False


def test_evaluator_returns_normalized_canonical_result() -> None:
    result = GroundingExecutionAuthorizationEvaluator.evaluate(
        GroundingExecutionContextConsumptionDecisionResult("allowed", "ready", True)
    )
    assert isinstance(result, GroundingExecutionAuthorizationResult)
    assert result.to_dict() == {
        "status": "authorized",
        "grounding_status": "ready",
        "authorized": True,
        "reason": None,
        "authorization_executed": True,
    }


def test_unsupported_shape_is_rejected() -> None:
    try:
        GroundingExecutionAuthorizationResultNormalizer.normalize(object())
    except ValueError as exc:
        assert "result contract or mapping" in str(exc)
    else:
        raise AssertionError("unsupported authorization result should be rejected")


def test_invalid_mapping_is_rejected_by_contract() -> None:
    try:
        GroundingExecutionAuthorizationResultNormalizer.normalize(
            {"status": "authorized", "grounding_status": "ready", "authorized": False}
        )
    except ValueError as exc:
        assert "authorized status" in str(exc)
    else:
        raise AssertionError("inconsistent authorization mapping should be rejected")


def test_denied_mapping_without_reason_is_rejected() -> None:
    try:
        GroundingExecutionAuthorizationResultNormalizer.normalize(
            {"status": "denied", "grounding_status": "ready", "authorized": False}
        )
    except ValueError as exc:
        assert "reason" in str(exc)
    else:
        raise AssertionError("denied mapping without reason should be rejected")


def test_deterministic_serialization() -> None:
    result = GroundingExecutionAuthorizationResultNormalizer.normalize(
        {"status": "authorized", "grounding_status": "ready", "authorized": True}
    )
    assert result.to_dict() == {
        "status": "authorized",
        "grounding_status": "ready",
        "authorized": True,
        "reason": None,
        "authorization_executed": True,
    }
