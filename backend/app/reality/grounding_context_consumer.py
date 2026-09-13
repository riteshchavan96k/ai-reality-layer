from backend.app.reality.grounding_context_consumption import GroundingContextConsumption
from backend.app.reality.grounding_context_contract import GroundingContext


class GroundingContextConsumer:
    """Classify canonical grounding context before model execution."""

    def consume(self, grounding_context: object) -> GroundingContextConsumption:
        if not isinstance(grounding_context, GroundingContext):
            raise ValueError("grounding context must be a GroundingContext")

        if grounding_context.status == "ready":
            if grounding_context.source_count == 0 and not grounding_context.content:
                return GroundingContextConsumption.rejected_result(
                    "ready", "empty_grounding_context"
                )
            return GroundingContextConsumption.usable_result("ready")

        if grounding_context.status == "not_available":
            return GroundingContextConsumption.usable_result("not_available")

        return GroundingContextConsumption.rejected_result(
            "unknown", "unsupported_grounding_context_status"
        )


__all__ = ["GroundingContextConsumer"]
