from collections.abc import Mapping

from backend.app.execution.execution_trace_contract import ExecutionTraceEvent


class ExecutionTraceEventNormalizer:
    """Normalize trace events through the canonical execution-trace contract."""

    @staticmethod
    def normalize(raw_event: object) -> ExecutionTraceEvent:
        if isinstance(raw_event, ExecutionTraceEvent):
            return raw_event
        if not isinstance(raw_event, Mapping):
            raise ValueError("execution trace event must be a contract or mapping")

        value = dict(raw_event)
        metadata = value.pop("metadata", None)
        if metadata is None:
            metadata = {
                key: value.pop(key)
                for key in list(value)
                if key not in {"stage", "status", "timestamp"}
            }
        elif not isinstance(metadata, Mapping):
            raise ValueError("metadata must be a mapping")

        value["metadata"] = dict(metadata)
        return ExecutionTraceEvent.validate(value)


__all__ = ["ExecutionTraceEventNormalizer"]
