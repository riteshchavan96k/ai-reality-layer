from collections.abc import Mapping
from typing import Any

from backend.app.execution.outcome_memory_contract import OutcomeMemoryRecord


class OutcomeMemoryRecordNormalizer:
    """Canonical normalization boundary for stored execution outcomes."""

    @staticmethod
    def normalize(raw_record: object) -> OutcomeMemoryRecord:
        if isinstance(raw_record, OutcomeMemoryRecord):
            return OutcomeMemoryRecord.validate(raw_record)
        if isinstance(raw_record, Mapping):
            return OutcomeMemoryRecord.validate(raw_record)
        raise TypeError("outcome memory record must be a mapping or OutcomeMemoryRecord")


__all__ = ["OutcomeMemoryRecordNormalizer"]
