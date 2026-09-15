from backend.app.reality.grounding_execution_context_consumption_decision import (
    GroundingExecutionContextConsumptionDecision,
)
from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


class GroundingExecutionContextConsumptionDecisionEvaluator:
    """Derive the canonical decision result from execution-context consumption."""

    @staticmethod
    def evaluate(
        consumption: GroundingExecutionContextConsumptionResult,
    ) -> GroundingExecutionContextConsumptionDecisionResult:
        decision = GroundingExecutionContextConsumptionDecision.from_consumption(consumption)
        return GroundingExecutionContextConsumptionDecisionResult.from_decision(decision)


__all__ = ["GroundingExecutionContextConsumptionDecisionEvaluator"]
