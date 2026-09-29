import pytest

from backend.app.execution.execution_trace import ExecutionTrace
from backend.app.execution.execution_trace_contract import ExecutionTraceEvent
from backend.app.execution.execution_trace_snapshot_contract import ExecutionTraceSnapshot
from backend.app.execution.execution_trace_snapshot_normalizer import ExecutionTraceSnapshotNormalizer


def _event(stage: str = "retrieval") -> ExecutionTraceEvent:
    return ExecutionTraceEvent(
        stage=stage,
        status="completed",
        timestamp="2026-09-29T10:00:00+00:00",
        metadata={"source_count": 2},
    )


def test_step166_accepts_canonical_snapshot():
    snapshot = ExecutionTraceSnapshot.from_events([_event()])
    assert ExecutionTraceSnapshot.validate(snapshot) is snapshot
    assert snapshot.event_count == 1


def test_step166_normalizes_flat_event_mappings():
    snapshot = ExecutionTraceSnapshotNormalizer.normalize(
        [
            {
                "stage": "retrieval",
                "status": "completed",
                "timestamp": "2026-09-29T10:00:00+00:00",
                "source_count": 2,
            }
        ]
    )
    assert snapshot.event_count == 1
    assert snapshot.to_list()[0]["source_count"] == 2


def test_step166_rejects_non_collection_snapshot():
    with pytest.raises(ValueError, match="must be a list, tuple"):
        ExecutionTraceSnapshot.validate({"stage": "retrieval"})


def test_step166_rejects_invalid_event_inside_snapshot():
    with pytest.raises(ValueError, match="timezone information"):
        ExecutionTraceSnapshot.validate(
            [
                {
                    "stage": "retrieval",
                    "status": "completed",
                    "timestamp": "2026-09-29T10:00:00",
                    "metadata": {},
                }
            ]
        )


def test_step166_trace_snapshot_result_is_canonical():
    trace = ExecutionTrace()
    trace.record("retrieval", "completed", source_count=2)
    trace.record("model_execution", "completed", model="test-model")

    snapshot = trace.snapshot_result()

    assert isinstance(snapshot, ExecutionTraceSnapshot)
    assert snapshot.event_count == 2
    assert snapshot.events[0].stage == "retrieval"
    assert snapshot.events[1].stage == "model_execution"


def test_step166_legacy_snapshot_api_is_preserved():
    trace = ExecutionTrace()
    trace.record("retrieval", "completed", source_count=2)

    snapshot = trace.snapshot()

    assert isinstance(snapshot, list)
    assert snapshot[0]["stage"] == "retrieval"
    assert snapshot[0]["source_count"] == 2
