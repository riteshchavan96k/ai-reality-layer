from dataclasses import dataclass

from backend.app.reality.grounding_execution_context import GroundingExecutionContext


@dataclass(frozen=True)
class GroundingExecutionContextConsumption:
    """Canonical decision describing whether an execution context is usable."""

    status: str
    grounding_status: str
    usable: bool
    reason: str | None = None
    consumption_executed: bool = True

    def __post_init__(self) -> None:
        if self.status not in {"usable", "rejected"}:
            raise ValueError("status must be usable or rejected")
        if self.grounding_status not in {"ready", "not_available"}:
            raise ValueError("grounding_status must be ready or not_available")
        if not isinstance(self.usable, bool):
            raise ValueError("usable must be a boolean")
        if not isinstance(self.consumption_executed, bool):
            raise ValueError("consumption_executed must be a boolean")
        if self.status == "usable" and not self.usable:
            raise ValueError("usable status requires usable=True")
        if self.status == "rejected" and self.usable:
            raise ValueError("rejected status requires usable=False")
        if self.usable and self.reason is not None:
            raise ValueError("usable context consumption cannot contain a reason")
        if not self.usable and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise ValueError("rejected context consumption requires a reason")

    @classmethod
    def usable_result(cls, grounding_status: str) -> "GroundingExecutionContextConsumption":
        return cls("usable", grounding_status, True)

    @classmethod
    def rejected_result(cls, grounding_status: str, reason: str) -> "GroundingExecutionContextConsumption":
        return cls("rejected", grounding_status, False, reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "grounding_status": self.grounding_status,
            "usable": self.usable,
            "reason": self.reason,
            "consumption_executed": self.consumption_executed,
        }


class GroundingExecutionContextConsumer:
    """Validate the execution-facing context immediately before execution."""

    @staticmethod
    def consume(context: GroundingExecutionContext) -> GroundingExecutionContextConsumption:
        if not isinstance(context, GroundingExecutionContext):
            raise ValueError("execution context must be a GroundingExecutionContext")
        if not context.execution_allowed:
            return GroundingExecutionContextConsumption.rejected_result(
                context.grounding_status, "execution_not_allowed"
            )
        if not context.context_prepared:
            return GroundingExecutionContextConsumption.rejected_result(
                context.grounding_status, "execution_context_not_prepared"
            )
        if context.grounding_status == "ready":
            if context.source_count == 0 and not context.content:
                return GroundingExecutionContextConsumption.rejected_result(
                    "ready", "empty_grounding_execution_context"
                )
            return GroundingExecutionContextConsumption.usable_result("ready")
        if context.grounding_status == "not_available":
            return GroundingExecutionContextConsumption.usable_result("not_available")
        raise ValueError("unsupported grounding execution context status")


__all__ = ["GroundingExecutionContextConsumption", "GroundingExecutionContextConsumer"]
