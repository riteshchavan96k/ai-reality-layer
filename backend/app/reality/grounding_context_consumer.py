from backend.app.reality.grounding_context_consumption_result import GroundingContextConsumptionResult
from backend.app.reality.grounding_context_contract import GroundingContext


class GroundingContextConsumer:
    """Classify canonical grounding context before model execution."""

    def consume(self, grounding_context: object) -> GroundingContextConsumptionResult:
        if not isinstance(grounding_context, GroundingContext):
            raise ValueError("grounding context must be a GroundingContext")

        if grounding_context.status == "ready":
            if grounding_context.source_count == 0 and not grounding_context.content:
                return GroundingContextConsumptionResult.rejected_result(
                    "ready", "empty_grounding_context"
                )
            return GroundingContextConsumptionResult.usable_result("ready")

        if grounding_context.status == "not_available":
            return GroundingContextConsumptionResult.usable_result("not_available")

        raise ValueError("unsupported grounding context status")


__all__ = ["GroundingContextConsumer"]
