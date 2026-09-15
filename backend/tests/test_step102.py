import pytest

from backend.app.reality.grounding_execution_context import GroundingExecutionContext
from backend.app.reality.grounding_execution_context_consumption import GroundingExecutionContextConsumer
from backend.app.reality.grounding_execution_context_consumption_result import GroundingExecutionContextConsumptionResult


def ready_context(**overrides):
    values = {
        "task": "What is the current status?",
        "grounding_status": "ready",
        "content": "Evidence-backed context.",
        "sources": [{"title": "Source A", "uri": "https://example.com/a"}],
        "source_count": 1,
        "execution_allowed": True,
        "context_prepared": True,
    }
    values.update(overrides)
    return GroundingExecutionContext(**values)


def test_consumer_returns_canonical_result_for_ready_context():
    result = GroundingExecutionContextConsumer.consume(ready_context())
    assert isinstance(result, GroundingExecutionContextConsumptionResult)
    assert result.status == "usable"
    assert result.grounding_status == "ready"
    assert result.usable is True
    assert result.reason is None
    assert result.consumption_executed is True


def test_consumer_returns_canonical_result_for_not_available_context():
    context = GroundingExecutionContext.not_available_result("Explain this")
    result = GroundingExecutionContextConsumer.consume(context)
    assert result == GroundingExecutionContextConsumptionResult.usable_result("not_available")


def test_execution_permission_rejection_is_preserved():
    result = GroundingExecutionContextConsumer.consume(ready_context(execution_allowed=False))
    assert result.status == "rejected"
    assert result.usable is False
    assert result.reason == "execution_not_allowed"


def test_preparation_rejection_is_preserved():
    result = GroundingExecutionContextConsumer.consume(ready_context(context_prepared=False))
    assert result.status == "rejected"
    assert result.reason == "execution_context_not_prepared"


def test_empty_ready_context_is_rejected():
    result = GroundingExecutionContextConsumer.consume(ready_context(content=None, sources=[], source_count=0))
    assert result.status == "rejected"
    assert result.reason == "empty_grounding_execution_context"


def test_result_contract_rejects_inconsistent_usable_state():
    with pytest.raises(ValueError, match="usable status requires usable=True"):
        GroundingExecutionContextConsumptionResult(
            status="usable",
            grounding_status="ready",
            usable=False,
        )


def test_result_contract_rejects_missing_rejection_reason():
    with pytest.raises(ValueError, match="requires a reason"):
        GroundingExecutionContextConsumptionResult(
            status="rejected",
            grounding_status="ready",
            usable=False,
            reason=None,
        )


def test_result_contract_rejects_invalid_grounding_status():
    with pytest.raises(ValueError, match="grounding_status must be ready or not_available"):
        GroundingExecutionContextConsumptionResult(
            status="usable",
            grounding_status="invalid",
            usable=True,
        )


def test_result_serialization_is_deterministic():
    result = GroundingExecutionContextConsumptionResult.usable_result("ready")
    assert result.to_dict() == {
        "status": "usable",
        "grounding_status": "ready",
        "usable": True,
        "reason": None,
        "consumption_executed": True,
    }
