from backend.app.reality.grounding_execution_context_consumption_decision import (
    GroundingExecutionContextConsumptionDecision,
)
from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


class GroundingExecutionContextConsumptionDecisionEvaluator:
    """Derive the execution decision from the canonical consumption result."""

    @staticmethod
    def evaluate(
        consumption: GroundingExecutionContextConsumptionResult,
    ) -> GroundingExecutionContextConsumptionDecision:
        return GroundingExecutionContextConsumptionDecision.from_consumption(consumption)


__all__ = ["GroundingExecutionContextConsumptionDecisionEvaluator"]
