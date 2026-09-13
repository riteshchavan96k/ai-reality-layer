import pytest

from backend.app.reality.grounding_context_consumption_result import GroundingContextConsumptionResult
from backend.app.reality.grounding_context_consumer import GroundingContextConsumer
from backend.app.reality.grounding_context_contract import GroundingContext


def test_consumer_returns_typed_result_for_ready_context() -> None:
    result = GroundingContextConsumer().consume(GroundingContext.ready_result("Task", "Evidence", []))
    assert isinstance(result, GroundingContextConsumptionResult)
    assert result.status == "usable"
    assert result.grounding_status == "ready"


def test_consumer_returns_typed_rejection_for_empty_ready_context() -> None:
    result = GroundingContextConsumer().consume(GroundingContext.ready_result("Task", None, []))
    assert isinstance(result, GroundingContextConsumptionResult)
    assert result.status == "rejected"
    assert result.reason == "empty_grounding_context"


def test_not_available_result_is_typed_and_usable() -> None:
    result = GroundingContextConsumer().consume(GroundingContext.not_available_result("Task"))
    assert result == GroundingContextConsumptionResult.usable_result("not_available")


def test_result_rejects_inconsistent_state() -> None:
    with pytest.raises(ValueError, match="rejected status requires usable=False"):
        GroundingContextConsumptionResult(status="rejected", grounding_status="ready", usable=True)


def test_result_rejects_invalid_grounding_status() -> None:
    with pytest.raises(ValueError, match="grounding_status must be ready or not_available"):
        GroundingContextConsumptionResult(status="usable", grounding_status="unknown", usable=True)


def test_result_serialization_is_deterministic() -> None:
    result = GroundingContextConsumptionResult.rejected_result("ready", "empty_grounding_context")
    assert result.to_dict() == {
        "status": "rejected", "grounding_status": "ready", "usable": False,
        "reason": "empty_grounding_context", "consumption_executed": True,
    }
