import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumer,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
)


def test_consumer_returns_canonical_consumption_result():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result()
    )
    assert isinstance(
        result,
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
    )
    assert result.status == "usable"
    assert result.authorization_status == "authorized"
    assert result.allowed is True
    assert result.reason is None
    assert result.decision_executed is True
    assert result.consumption_executed is True


def test_blocked_result_is_canonical_and_preserves_reason():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResult.blocked_result(
            "denied", "authorization_denied"
        )
    )
    assert isinstance(
        result,
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
    )
    assert result.status == "rejected"
    assert result.authorization_status == "denied"
    assert result.allowed is False
    assert result.reason == "authorization_denied"


def test_canonical_result_rejects_inconsistent_status():
    with pytest.raises(ValueError, match="usable status requires allowed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "authorized", False
        )


def test_canonical_result_rejects_inconsistent_authorization_status():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "denied", True
        )


def test_canonical_result_rejects_missing_rejection_reason():
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "rejected", "denied", False
        )


def test_canonical_result_rejects_unexecuted_decision():
    with pytest.raises(ValueError, match="decision_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "authorized", True, decision_executed=False
        )


def test_canonical_result_rejects_unexecuted_consumption():
    with pytest.raises(ValueError, match="consumption_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "authorized", True, consumption_executed=False
        )


def test_canonical_result_rejects_non_boolean_execution_state():
    with pytest.raises(ValueError, match="decision_executed must be a boolean"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "authorized", True, decision_executed="yes"
        )
    with pytest.raises(ValueError, match="consumption_executed must be a boolean"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult(
            "usable", "authorized", True, consumption_executed="yes"
        )


def test_canonical_result_serialization_is_deterministic():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult.usable_result()
    assert result.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
        "consumption_executed": True,
    }


def test_consumer_rejects_unexecuted_decision_result():
    decision = GroundingExecutionAuthorizationConsumptionDecisionResult(
        "allowed", "authorized", True, decision_executed=False
    )
    with pytest.raises(ValueError, match="decision_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(decision)
