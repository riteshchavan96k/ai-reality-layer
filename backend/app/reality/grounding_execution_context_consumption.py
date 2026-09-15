from backend.app.reality.grounding_execution_context import GroundingExecutionContext
from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


class GroundingExecutionContextConsumer:
    """Validate the execution-facing context immediately before execution."""

    @staticmethod
    def consume(context: GroundingExecutionContext) -> GroundingExecutionContextConsumptionResult:
        if not isinstance(context, GroundingExecutionContext):
            raise ValueError("execution context must be a GroundingExecutionContext")
        if not context.execution_allowed:
            return GroundingExecutionContextConsumptionResult.rejected_result(
                context.grounding_status, "execution_not_allowed"
            )
        if not context.context_prepared:
            return GroundingExecutionContextConsumptionResult.rejected_result(
                context.grounding_status, "execution_context_not_prepared"
            )
        if context.grounding_status == "ready":
            if context.source_count == 0 and not context.content:
                return GroundingExecutionContextConsumptionResult.rejected_result(
                    "ready", "empty_grounding_execution_context"
                )
            return GroundingExecutionContextConsumptionResult.usable_result("ready")
        if context.grounding_status == "not_available":
            return GroundingExecutionContextConsumptionResult.usable_result("not_available")
        raise ValueError("unsupported grounding execution context status")


__all__ = ["GroundingExecutionContextConsumer"]
