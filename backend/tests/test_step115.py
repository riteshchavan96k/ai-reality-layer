import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_normalizer import (
    GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer,
)


def test_typed_result_is_preserved():
    result = GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result("authorized")
    assert GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(result) is result


def test_allowed_mapping_is_normalized():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
        {"status": "allowed", "authorization_status": "authorized", "allowed": True}
    )
    assert isinstance(result, GroundingExecutionAuthorizationConsumptionDecisionResult)
    assert result.to_dict() == {
        "status": "allowed",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }


def test_blocked_mapping_preserves_reason():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
        {
            "status": "blocked",
            "authorization_status": "denied",
            "allowed": False,
            "reason": "authorization_denied",
        }
    )
    assert result.reason == "authorization_denied"


def test_explicit_decision_state_is_preserved():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
        {
            "status": "allowed",
            "authorization_status": "authorized",
            "allowed": True,
            "decision_executed": False,
        }
    )
    assert result.decision_executed is False


def test_invalid_mapping_is_rejected_by_contract():
    with pytest.raises(ValueError, match="allowed status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
            {"status": "allowed", "authorization_status": "authorized", "allowed": False}
        )


def test_non_mapping_is_rejected():
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(object())


def test_invalid_authorization_status_is_rejected():
    with pytest.raises(ValueError, match="authorization_status must be"):
        GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
            {"status": "allowed", "authorization_status": "invalid", "allowed": True}
        )


def test_blocked_mapping_requires_reason():
    with pytest.raises(ValueError, match="blocked decision requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
            {"status": "blocked", "authorization_status": "denied", "allowed": False}
        )


def test_authorization_state_must_match_allowed_state():
    with pytest.raises(ValueError, match="authorized status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
            {"status": "blocked", "authorization_status": "authorized", "allowed": False, "reason": "blocked"}
        )


def test_serialization_is_deterministic():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultNormalizer.normalize(
        {"status": "allowed", "authorization_status": "authorized", "allowed": True}
    )
    assert result.to_dict() == GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result("authorized").to_dict()
