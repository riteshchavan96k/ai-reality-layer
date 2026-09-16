import pytest

from backend.app.reality.grounding_execution_authorization_consumer import (
    GroundingExecutionAuthorizationConsumer,
)
from backend.app.reality.grounding_execution_authorization_consumption import (
    GroundingExecutionAuthorizationConsumption,
)
from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)
from backend.app.reality.grounding_execution_authorization_result import (
    GroundingExecutionAuthorizationResult,
)


def test_consumer_returns_canonical_result_for_authorized_result() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.authorized_result("ready")
    )
    assert isinstance(result, GroundingExecutionAuthorizationConsumptionResult)
    assert result.status == "usable"
    assert result.authorization_status == "authorized"
    assert result.usable is True
    assert result.reason is None
    assert result.consumption_executed is True


def test_consumer_returns_canonical_result_for_denied_result() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.denied_result(
            "ready", "execution_not_authorized"
        )
    )
    assert isinstance(result, GroundingExecutionAuthorizationConsumptionResult)
    assert result.status == "rejected"
    assert result.authorization_status == "denied"
    assert result.usable is False
    assert result.reason == "execution_not_authorized"
    assert result.consumption_executed is True


def test_not_available_authorized_result_remains_usable() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.authorized_result("not_available")
    )
    assert result == GroundingExecutionAuthorizationConsumptionResult.usable_result(
        "authorized"
    )


def test_consumer_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="GroundingExecutionAuthorizationResult"):
        GroundingExecutionAuthorizationConsumer.consume(object())


def test_legacy_consumption_name_is_compatible_alias() -> None:
    assert GroundingExecutionAuthorizationConsumption is GroundingExecutionAuthorizationConsumptionResult


def test_result_contract_rejects_inconsistent_usable_state() -> None:
    with pytest.raises(ValueError, match="denied status"):
        GroundingExecutionAuthorizationConsumptionResult(
            status="usable",
            authorization_status="denied",
            usable=True,
        )


def test_result_contract_rejects_authorized_rejection() -> None:
    with pytest.raises(ValueError, match="authorized status"):
        GroundingExecutionAuthorizationConsumptionResult(
            status="rejected",
            authorization_status="authorized",
            usable=False,
            reason="invalid_authorization",
        )


def test_result_contract_rejects_rejected_result_without_reason() -> None:
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionAuthorizationConsumptionResult(
            status="rejected",
            authorization_status="denied",
            usable=False,
        )


def test_result_contract_rejects_invalid_authorization_status() -> None:
    with pytest.raises(
        ValueError,
        match="authorization_status must be authorized or denied",
    ):
        GroundingExecutionAuthorizationConsumptionResult(
            status="usable",
            authorization_status="invalid",
            usable=True,
        )


def test_result_contract_rejects_non_boolean_execution_state() -> None:
    with pytest.raises(ValueError, match="consumption_executed must be a boolean"):
        GroundingExecutionAuthorizationConsumptionResult(
            status="usable",
            authorization_status="authorized",
            usable=True,
            consumption_executed="yes",
        )


def test_result_serialization_is_deterministic() -> None:
    result = GroundingExecutionAuthorizationConsumptionResult.usable_result(
        "authorized"
    )
    assert result.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "usable": True,
        "reason": None,
        "consumption_executed": True,
    }
