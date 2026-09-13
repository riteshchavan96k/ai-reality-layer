import pytest

from backend.app.reality.grounding_context_consumption import GroundingContextConsumption
from backend.app.reality.grounding_context_consumer import GroundingContextConsumer
from backend.app.reality.grounding_context_contract import GroundingContext


def test_ready_context_is_usable() -> None:
    context = GroundingContext.ready_result("Task", "Evidence", [])
    result = GroundingContextConsumer().consume(context)
    assert result.status == "usable"
    assert result.grounding_status == "ready"
    assert result.usable is True


def test_ready_context_with_sources_is_usable() -> None:
    context = GroundingContext.ready_result("Task", None, [{"title": "A", "uri": "u"}])
    result = GroundingContextConsumer().consume(context)
    assert result.to_dict() == {
        "status": "usable",
        "grounding_status": "ready",
        "usable": True,
        "reason": None,
        "consumption_executed": True,
    }


def test_empty_ready_context_is_rejected() -> None:
    context = GroundingContext.ready_result("Task", None, [])
    result = GroundingContextConsumer().consume(context)
    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "empty_grounding_context"


def test_not_available_context_is_usable_for_execution() -> None:
    context = GroundingContext.not_available_result("Task")
    result = GroundingContextConsumer().consume(context)
    assert result.status == "usable"
    assert result.grounding_status == "not_available"
    assert result.usable is True


def test_invalid_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="grounding context must be a GroundingContext"):
        GroundingContextConsumer().consume({"status": "ready"})


def test_consumption_contract_validation_is_deterministic() -> None:
    with pytest.raises(ValueError, match="usable status requires usable=True"):
        GroundingContextConsumption(
            status="usable",
            grounding_status="ready",
            usable=False,
        )


def test_rejected_consumption_requires_false_usable() -> None:
    with pytest.raises(ValueError, match="rejected status requires usable=False"):
        GroundingContextConsumption(
            status="rejected",
            grounding_status="ready",
            usable=True,
        )


def test_serialization_is_deterministic() -> None:
    result = GroundingContextConsumption.rejected_result("ready", "empty_grounding_context")
    assert result.to_dict() == {
        "status": "rejected",
        "grounding_status": "ready",
        "usable": False,
        "reason": "empty_grounding_context",
        "consumption_executed": True,
    }
