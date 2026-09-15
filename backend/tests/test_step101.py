import pytest

from backend.app.reality.grounding_execution_context import GroundingExecutionContext
from backend.app.reality.grounding_execution_context_consumption import (
    GroundingExecutionContextConsumer,
)


def ready_context(**kwargs) -> GroundingExecutionContext:
    values = {
        "task": "Check current evidence",
        "grounding_status": "ready",
        "content": "Verified evidence",
        "sources": [{"title": "Source A"}],
        "source_count": 1,
    }
    values.update(kwargs)
    return GroundingExecutionContext(**values)


def test_ready_context_is_usable() -> None:
    result = GroundingExecutionContextConsumer.consume(ready_context())
    assert result.status == "usable"
    assert result.usable is True
    assert result.grounding_status == "ready"
    assert result.reason is None


def test_not_available_context_remains_usable() -> None:
    context = GroundingExecutionContext.not_available_result("Explain a general concept")
    result = GroundingExecutionContextConsumer.consume(context)
    assert result.status == "usable"
    assert result.usable is True
    assert result.grounding_status == "not_available"


def test_empty_ready_context_is_rejected() -> None:
    context = ready_context(content=None, sources=[], source_count=0)
    result = GroundingExecutionContextConsumer.consume(context)
    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "empty_grounding_execution_context"


def test_execution_permission_is_enforced() -> None:
    context = ready_context(execution_allowed=False)
    result = GroundingExecutionContextConsumer.consume(context)
    assert result.status == "rejected"
    assert result.reason == "execution_not_allowed"


def test_preparation_state_is_enforced() -> None:
    context = ready_context(context_prepared=False)
    result = GroundingExecutionContextConsumer.consume(context)
    assert result.status == "rejected"
    assert result.reason == "execution_context_not_prepared"


def test_invalid_input_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be a GroundingExecutionContext"):
        GroundingExecutionContextConsumer.consume({})  # type: ignore[arg-type]


def test_deterministic_serialization() -> None:
    result = GroundingExecutionContextConsumer.consume(ready_context())
    assert result.to_dict() == {
        "status": "usable",
        "grounding_status": "ready",
        "usable": True,
        "reason": None,
        "consumption_executed": True,
    }
