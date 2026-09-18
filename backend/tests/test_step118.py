import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
 )
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_normalizer import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer,
 )


def test_typed_result_passes_through_unchanged():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult.usable_result()
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize(result)
    assert normalized is result


def test_allowed_mapping_normalizes_to_canonical_result():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({
        "status": "usable",
        "authorization_status": "authorized",
        "allowed": True,
    })
    assert isinstance(normalized, GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult)
    assert normalized.to_dict() == {
        "status": "usable", "authorization_status": "authorized", "allowed": True,
        "reason": None, "decision_executed": True, "consumption_executed": True,
    }


def test_rejected_mapping_preserves_reason_and_execution_state():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({
        "status": "rejected", "authorization_status": "denied", "allowed": False,
        "reason": "authorization_denied", "decision_executed": True, "consumption_executed": True,
    })
    assert normalized.status == "rejected"
    assert normalized.reason == "authorization_denied"
    assert normalized.decision_executed is True
    assert normalized.consumption_executed is True


def test_invalid_mapping_state_is_rejected():
    with pytest.raises(ValueError, match="usable status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({"status":"usable","authorization_status":"authorized","allowed":False})


def test_denied_mapping_must_be_blocked():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({"status":"usable","authorization_status":"denied","allowed":True})


def test_rejected_mapping_requires_reason():
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({"status":"rejected","authorization_status":"denied","allowed":False})


def test_unexecuted_decision_is_rejected():
    with pytest.raises(ValueError, match="decision result consumption requires decision_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({"status":"usable","authorization_status":"authorized","allowed":True,"decision_executed":False})


def test_unexecuted_consumption_is_rejected():
    with pytest.raises(ValueError, match="decision result consumption requires consumption_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({"status":"usable","authorization_status":"authorized","allowed":True,"consumption_executed":False})


def test_non_mapping_input_is_rejected():
    with pytest.raises(ValueError, match="must be a result contract or mapping"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize("invalid")


def test_serialization_remains_deterministic():
    normalized = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultNormalizer.normalize({"status":"usable","authorization_status":"authorized","allowed":True})
    assert normalized.to_dict() == {
        "status": "usable", "authorization_status": "authorized", "allowed": True,
        "reason": None, "decision_executed": True, "consumption_executed": True,
    }
