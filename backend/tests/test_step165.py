import pytest

from backend.app.execution.execution_trace import ExecutionTrace
from backend.app.execution.execution_trace_contract import ExecutionTraceEvent
from backend.app.execution.execution_trace_normalizer import ExecutionTraceEventNormalizer


def test_step165_accepts_canonical_event():
    event = ExecutionTraceEvent(
        stage="retrieval",
        status="completed",
        timestamp="2026-09-29T10:00:00+00:00",
        metadata={"source_count": 2},
    )
    assert ExecutionTraceEvent.validate(event) is event


def test_step165_normalizes_flat_mapping_and_preserves_metadata():
    event = ExecutionTraceEventNormalizer.normalize(
        {
            "stage": "model_execution",
            "status": "completed",
            "timestamp": "2026-09-29T10:00:00+00:00",
            "model": "test-model",
            "attempts": 1,
        }
    )
    assert event.metadata == {"model": "test-model", "attempts": 1}


def test_step165_rejects_missing_required_field():
    with pytest.raises(ValueError, match="missing required fields"):
        ExecutionTraceEvent.validate(
            {
                "stage": "retrieval",
                "status": "completed",
                "timestamp": "2026-09-29T10:00:00+00:00",
            }
        )


def test_step165_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone information"):
        ExecutionTraceEvent(
            stage="retrieval",
            status="completed",
            timestamp="2026-09-29T10:00:00",
            metadata={},
        )


def test_step165_rejects_invalid_timestamp():
    with pytest.raises(ValueError, match="valid ISO-8601"):
        ExecutionTraceEvent(
            stage="retrieval",
            status="completed",
            timestamp="not-a-timestamp",
            metadata={},
        )


def test_step165_execution_trace_records_validated_events():
    trace = ExecutionTrace()
    trace.record("retrieval", "completed", source_count=2)
    trace.record("model_execution", "completed", model="test-model")

    snapshot = trace.snapshot()

    assert len(snapshot) == 2
    assert snapshot[0]["stage"] == "retrieval"
    assert snapshot[0]["source_count"] == 2
    assert snapshot[1]["model"] == "test-model"
    assert snapshot[0]["timestamp"].endswith("+00:00")
