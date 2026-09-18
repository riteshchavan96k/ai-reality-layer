import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult,
)


def test_from_consumption_preserves_usable_state():
    source = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption(
        "usable",
        "authorized",
        True,
        decision_executed=True,
        consumption_executed=True,
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.from_consumption(
        source
    )
    assert result.status == "usable"
    assert result.authorization_status == "authorized"
    assert result.allowed is True
    assert result.reason is None
    assert result.decision_executed is True
    assert result.consumption_executed is True


def test_from_consumption_preserves_rejected_reason():
    source = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption(
        "rejected",
        "denied",
        False,
        "authorization_decision_rejected",
        decision_executed=True,
        consumption_executed=True,
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.from_consumption(
        source
    )
    assert result.status == "rejected"
    assert result.authorization_status == "denied"
    assert result.allowed is False
    assert result.reason == "authorization_decision_rejected"


def test_from_consumption_rejects_wrong_input_type():
    with pytest.raises(
        ValueError,
        match="must be a GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption",
    ):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.from_consumption(
            object()
        )


def test_result_rejects_unexecuted_decision():
    with pytest.raises(ValueError, match="decision result consumption requires decision_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult(
            "usable",
            "authorized",
            True,
            decision_executed=False,
            consumption_executed=True,
        )


def test_result_rejects_unexecuted_consumption():
    with pytest.raises(ValueError, match="decision result consumption requires consumption_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult(
            "usable",
            "authorized",
            True,
            decision_executed=True,
            consumption_executed=False,
        )


def test_result_rejects_reason_on_usable_state():
    with pytest.raises(ValueError, match="cannot contain a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult(
            "usable",
            "authorized",
            True,
            "unexpected",
        )


def test_result_requires_reason_on_rejected_state():
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult(
            "rejected",
            "denied",
            False,
        )


def test_result_enforces_authorization_consistency():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult(
            "usable",
            "denied",
            True,
        )


def test_factory_methods_create_canonical_results():
    usable = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.usable_result()
    rejected = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.rejected_result(
        "denied",
        "blocked_by_authorization",
    )
    assert usable.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
        "consumption_executed": True,
    }
    assert rejected.to_dict() == {
        "status": "rejected",
        "authorization_status": "denied",
        "allowed": False,
        "reason": "blocked_by_authorization",
        "decision_executed": True,
        "consumption_executed": True,
    }


def test_result_serialization_is_deterministic():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.usable_result()
    assert result.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
        "consumption_executed": True,
    }


def test_result_is_immutable():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult.usable_result()
    with pytest.raises(Exception):
        result.allowed = False


def test_consumer_now_returns_canonical_step123_result():
    from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption import (
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer,
    )

    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result()
    )
    assert isinstance(
        result,
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult,
    )
