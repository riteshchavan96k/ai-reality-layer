from datetime import datetime, timezone

import pytest

from backend.app.execution.outcome_memory import OutcomeMemory
from backend.app.execution.outcome_memory_contract import OutcomeMemoryRecord
from backend.app.execution.outcome_memory_normalizer import OutcomeMemoryRecordNormalizer
from backend.app.execution.persistent_outcome_memory import PersistentOutcomeMemory


def _record(**overrides):
    value = {
        "record_id": 1,
        "task_fingerprint": "a" * 64,
        "task_type": "general",
        "routed_model": "mock-model",
        "executed_model": "mock-model",
        "execution_status": "success",
        "evaluation_score": 0.8,
        "attempts": 1,
        "total_attempts": 1,
        "budget_limit": 2,
        "fallback_used": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    value.update(overrides)
    return value


def test_canonical_record_accepts_valid_mapping():
    result = OutcomeMemoryRecord.validate(_record())
    assert result.executed_model == "mock-model"
    assert result.to_dict()["record_id"] == 1


def test_normalizer_accepts_canonical_record():
    record = OutcomeMemoryRecord.validate(_record())
    assert OutcomeMemoryRecordNormalizer.normalize(record) is record


def test_missing_required_field_is_rejected():
    value = _record()
    value.pop("timestamp")
    with pytest.raises(ValueError, match="missing fields"):
        OutcomeMemoryRecordNormalizer.normalize(value)


def test_invalid_fingerprint_is_rejected():
    with pytest.raises(ValueError, match="SHA-256"):
        OutcomeMemoryRecord.validate(_record(task_fingerprint="not-a-hash"))


def test_attempts_cannot_exceed_total_attempts():
    with pytest.raises(ValueError, match="attempts cannot exceed"):
        OutcomeMemoryRecord.validate(_record(attempts=3, total_attempts=2))


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone"):
        OutcomeMemoryRecord.validate(_record(timestamp="2026-09-29T12:00:00"))


def test_success_requires_executed_model():
    with pytest.raises(ValueError, match="executed_model"):
        OutcomeMemoryRecord.validate(_record(executed_model=None))


def test_in_memory_outcome_memory_records_canonical_result():
    memory = OutcomeMemory(max_records=2)
    record = memory.record(
        "test task",
        {"task_type": "general"},
        {"model": "mock-model"},
        {
            "model": "mock-model",
            "status": "success",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 2,
            "fallback_used": False,
        },
        {"score": 0.9},
    )
    assert OutcomeMemoryRecordNormalizer.normalize(record).execution_status == "success"
    assert len(memory.recent()) == 1


def test_persistent_outcome_memory_records_canonical_result(tmp_path):
    memory = PersistentOutcomeMemory(str(tmp_path / "outcomes.db"))
    record = memory.record(
        "test task",
        {"task_type": "general"},
        {"model": "mock-model"},
        {
            "model": "mock-model",
            "status": "success",
            "attempts": 1,
            "total_attempts": 1,
            "budget_limit": 2,
            "fallback_used": False,
        },
        None,
    )
    assert OutcomeMemoryRecordNormalizer.normalize(record).record_id == 1
    assert memory.recent(1)[0]["execution_status"] == "success"
