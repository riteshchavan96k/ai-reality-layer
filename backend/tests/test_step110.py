from backend.app.reality.grounding_execution_authorization_consumer import GroundingExecutionAuthorizationConsumer
from backend.app.reality.grounding_execution_authorization_consumption import GroundingExecutionAuthorizationConsumption
from backend.app.reality.grounding_execution_authorization_result import GroundingExecutionAuthorizationResult


def test_authorized_result_is_usable() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.authorized_result("ready")
    )
    assert result.status == "usable"
    assert result.usable is True
    assert result.authorization_status == "authorized"
    assert result.reason is None


def test_denied_result_is_rejected() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.denied_result(
            "ready", "execution_not_authorized"
        )
    )
    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "execution_not_authorized"


def test_not_available_authorized_result_remains_usable() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.authorized_result("not_available")
    )
    assert result.usable is True
    assert result.authorization_status == "authorized"


def test_consumer_rejects_invalid_input() -> None:
    try:
        GroundingExecutionAuthorizationConsumer.consume(object())
    except ValueError as exc:
        assert "GroundingExecutionAuthorizationResult" in str(exc)
    else:
        raise AssertionError("invalid authorization result should be rejected")


def test_consumption_executed_is_true() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.authorized_result("ready")
    )
    assert result.consumption_executed is True


def test_rejected_result_preserves_authorization_status() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.denied_result(
            "not_available", "execution_not_authorized"
        )
    )
    assert result.authorization_status == "denied"
    assert result.reason == "execution_not_authorized"


def test_contract_rejects_inconsistent_usable_authorization() -> None:
    try:
        GroundingExecutionAuthorizationConsumption(
            "usable", "denied", True
        )
    except ValueError as exc:
        assert "denied status" in str(exc)
    else:
        raise AssertionError("inconsistent authorization consumption should fail")


def test_contract_rejects_rejected_result_without_reason() -> None:
    try:
        GroundingExecutionAuthorizationConsumption(
            "rejected", "denied", False
        )
    except ValueError as exc:
        assert "reason" in str(exc)
    else:
        raise AssertionError("rejected consumption without reason should fail")


def test_deterministic_serialization() -> None:
    result = GroundingExecutionAuthorizationConsumer.consume(
        GroundingExecutionAuthorizationResult.authorized_result("ready")
    )
    assert result.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "usable": True,
        "reason": None,
        "consumption_executed": True,
    }
