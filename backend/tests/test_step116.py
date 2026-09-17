from backend.app.reality.grounding_execution_authorization_consumption_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumer,
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumption,
)


def test_allowed_decision_result_is_usable() -> None:
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result()
    )
    assert result.status == "usable"
    assert result.allowed is True
    assert result.authorization_status == "authorized"
    assert result.reason is None
    assert result.decision_executed is True
    assert result.consumption_executed is True


def test_blocked_decision_result_is_rejected() -> None:
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResult.blocked_result(
            "denied", "execution_not_authorized"
        )
    )
    assert result.status == "rejected"
    assert result.allowed is False
    assert result.authorization_status == "denied"
    assert result.reason == "execution_not_authorized"


def test_blocked_reason_is_preserved() -> None:
    decision = GroundingExecutionAuthorizationConsumptionDecisionResult(
        status="blocked",
        authorization_status="denied",
        allowed=False,
        reason="upstream_grounding_policy_blocked",
        decision_executed=True,
    )
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(
        decision
    )
    assert result.reason == "upstream_grounding_policy_blocked"


def test_consumer_rejects_wrong_input_type() -> None:
    try:
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(object())
    except ValueError as exc:
        assert "GroundingExecutionAuthorizationConsumptionDecisionResult" in str(exc)
    else:
        raise AssertionError("invalid decision result should be rejected")


def test_decision_execution_must_be_complete_before_consumption() -> None:
    try:
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumption(
            status="usable",
            authorization_status="authorized",
            allowed=True,
            decision_executed=False,
        )
    except ValueError as exc:
        assert "decision_executed" in str(exc)
    else:
        raise AssertionError("unexecuted decision should not be consumable")


def test_usable_consumption_cannot_have_reason() -> None:
    try:
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumption(
            status="usable",
            authorization_status="authorized",
            allowed=True,
            reason="unexpected_reason",
        )
    except ValueError as exc:
        assert "cannot contain a reason" in str(exc)
    else:
        raise AssertionError("usable consumption with a reason should fail")


def test_rejected_consumption_requires_reason() -> None:
    try:
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumption(
            status="rejected",
            authorization_status="denied",
            allowed=False,
        )
    except ValueError as exc:
        assert "requires a reason" in str(exc)
    else:
        raise AssertionError("rejected consumption without a reason should fail")


def test_authorization_status_must_match_allowed_state() -> None:
    try:
        GroundingExecutionAuthorizationConsumptionDecisionResultConsumption(
            status="usable",
            authorization_status="denied",
            allowed=True,
        )
    except ValueError as exc:
        assert "denied status" in str(exc)
    else:
        raise AssertionError("inconsistent authorization state should fail")


def test_consumption_executed_is_true() -> None:
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result()
    )
    assert result.consumption_executed is True


def test_deterministic_serialization() -> None:
    result = GroundingExecutionAuthorizationConsumptionDecisionResultConsumer.consume(
        GroundingExecutionAuthorizationConsumptionDecisionResult.allowed_result()
    )
    assert result.to_dict() == {
        "status": "usable",
        "authorization_status": "authorized",
        "allowed": True,
        "reason": None,
        "decision_executed": True,
        "consumption_executed": True,
    }
