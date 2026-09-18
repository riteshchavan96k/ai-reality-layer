import pytest

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer,
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption,
)


def test_allowed_result_is_usable():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result()
    )
    assert result.status == "usable"
    assert result.authorization_status == "authorized"
    assert result.allowed is True
    assert result.reason is None
    assert result.decision_executed is True
    assert result.consumption_executed is True


def test_blocked_result_is_rejected_and_reason_is_preserved():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.blocked_result(
            "denied", "authorization_decision_rejected"
        )
    )
    assert result.status == "rejected"
    assert result.authorization_status == "denied"
    assert result.allowed is False
    assert result.reason == "authorization_decision_rejected"


def test_wrong_input_type_is_rejected():
    with pytest.raises(ValueError, match="must be a GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer.consume(object())


def test_unexecuted_decision_result_is_rejected():
    with pytest.raises(ValueError, match="decision result must have decision_executed=True"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption.from_decision_result(
            GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
                "allowed", "authorized", True, decision_executed=False
            )
        )


def test_usable_consumption_cannot_have_reason():
    with pytest.raises(ValueError, match="cannot contain a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption(
            "usable", "authorized", True, "unexpected"
        )


def test_rejected_consumption_requires_reason():
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption(
            "rejected", "denied", False
        )


def test_authorization_state_must_match_allowed_state():
    with pytest.raises(ValueError, match="denied status requires allowed=False"):
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption(
            "usable", "denied", True
        )


def test_explicit_execution_flags_are_preserved():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumption.usable_result(
        decision_executed=True, consumption_executed=False
    )
    assert result.decision_executed is True
    assert result.consumption_executed is False


def test_deterministic_serialization():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result()
    )
    assert result.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
        "consumption_executed": True,
    }


def test_immutable_consumption_contract():
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.allowed_result()
    )
    with pytest.raises(Exception):
        result.allowed = False


def test_default_orchestration_dependencies_wire_the_consumer():
    from backend.app.orchestrator.dependencies import OrchestrationDependencies

    dependencies = OrchestrationDependencies.default()
    assert isinstance(
        dependencies.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumer,
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer,
    )
