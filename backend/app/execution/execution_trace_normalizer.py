from collections.abc import Mapping

from backend.app.execution.execution_trace_contract import ExecutionTraceEvent


class ExecutionTraceEventNormalizer:
    """Normalize trace events through the canonical execution-trace contract."""

    @staticmethod
    def normalize(raw_event: object) -> ExecutionTraceEvent:
        if isinstance(raw_event, ExecutionTraceEvent):
            return raw_event
        if isinstance(raw_event, Mapping):
            value = dict(raw_event)
            metadata = value.pop("metadata", None)
            if metadata is None:
                metadata = value.pop("_metadata", {})
            value["metadata"] = metadata
            return ExecutionTraceEvent.validate(value)
        raise ValueError("execution trace event must be a contract or mapping")


__all__ = ["ExecutionTraceEventNormalizer"]
