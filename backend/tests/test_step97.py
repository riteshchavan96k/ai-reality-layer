import pytest

from backend.app.reality.grounding_context_consumption_result import GroundingContextConsumptionResult
from backend.app.reality.grounding_execution_gate import GroundingExecutionGate, GroundingExecutionGateResult


def test_usable_grounding_allows_execution() -> None:
    result = GroundingExecutionGate().evaluate(GroundingContextConsumptionResult.usable_result("ready"))
    assert isinstance(result, GroundingExecutionGateResult)
    assert result.status == "allowed"
    assert result.allowed is True
    assert result.reason is None


def test_not_available_grounding_is_allowed_when_consumption_accepts_it() -> None:
    result = GroundingExecutionGate().evaluate(
        GroundingContextConsumptionResult.usable_result("not_available")
    )
    assert result.status == "allowed"
    assert result.grounding_status == "not_available"


def test_rejected_grounding_blocks_execution() -> None:
    result = GroundingExecutionGate().evaluate(
        GroundingContextConsumptionResult.rejected_result("ready", "empty_grounding_context")
    )
    assert result.status == "blocked"
    assert result.allowed is False
    assert result.reason == "empty_grounding_context"


def test_missing_rejection_reason_uses_stable_fallback() -> None:
    consumption = GroundingContextConsumptionResult(
        status="rejected",
        grounding_status="ready",
        usable=False,
        reason="grounding_rejected",
    )
    result = GroundingExecutionGate().evaluate(consumption)
    assert result.reason == "grounding_rejected"


def test_invalid_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="grounding consumption must be a GroundingContextConsumptionResult"):
        GroundingExecutionGate().evaluate({"status": "usable"})


def test_gate_contract_rejects_inconsistent_allowed_state() -> None:
    with pytest.raises(ValueError, match="allowed status requires allowed=True"):
        GroundingExecutionGateResult(
            status="allowed", grounding_status="ready", allowed=False
        )


def test_gate_contract_rejects_inconsistent_blocked_state() -> None:
    with pytest.raises(ValueError, match="blocked status requires allowed=False"):
        GroundingExecutionGateResult(
            status="blocked", grounding_status="ready", allowed=True
        )


def test_serialization_is_deterministic() -> None:
    result = GroundingExecutionGateResult.blocked_result("ready", "empty_grounding_context")
    assert result.to_dict() == {
        "status": "blocked",
        "grounding_status": "ready",
        "allowed": False,
        "reason": "empty_grounding_context",
        "gate_evaluated": True,
    }
