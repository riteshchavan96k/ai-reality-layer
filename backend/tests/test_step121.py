import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_normalizer import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer,
)


def test_typed_result_passes_through_unchanged():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result()
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(result)
    assert normalized is result


def test_allowed_mapping_normalizes_to_canonical_result():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
        {
            "status": "allowed",
            "authorization_status": "authorized",
            "allowed": True,
            "reason": None,
        }
    )
    assert normalized == GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result()


def test_blocked_mapping_normalizes_and_preserves_reason():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
        {
            "status": "blocked",
            "authorization_status": "denied",
            "allowed": False,
            "reason": "authorization_decision_rejected",
        }
    )
    assert normalized.status == "blocked"
    assert normalized.authorization_status == "denied"
    assert normalized.allowed is False
    assert normalized.reason == "authorization_decision_rejected"
    assert normalized.decision_executed is True


def test_mapping_preserves_explicit_execution_flag():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
        {
            "status": "allowed",
            "authorization_status": "authorized",
            "allowed": True,
            "reason": None,
            "decision_executed": False,
        }
    )
    assert normalized.decision_executed is False


def test_mapping_rejects_invalid_contract_state():
    with pytest.raises(ValueError, match="blocked decision result requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
            {
                "status": "blocked",
                "authorization_status": "denied",
                "allowed": False,
            }
        )


def test_mapping_rejects_inconsistent_authorization_state():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
            {
                "status": "allowed",
                "authorization_status": "denied",
                "allowed": True,
            }
        )


def test_mapping_rejects_invalid_status():
    with pytest.raises(ValueError, match="status must be allowed or blocked"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
            {
                "status": "unknown",
                "authorization_status": "authorized",
                "allowed": True,
            }
        )


def test_non_mapping_input_is_rejected():
    with pytest.raises(
        ValueError,
        match="must be a result contract or mapping",
    ):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
            "invalid"
        )


def test_serialization_remains_deterministic():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer.normalize(
        {
            "status": "allowed",
            "authorization_status": "authorized",
            "allowed": True,
        }
    )
    assert result.to_dict() == {
        "status": "allowed",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
    }
