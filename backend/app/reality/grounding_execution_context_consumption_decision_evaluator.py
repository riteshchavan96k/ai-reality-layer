from backend.app.reality.grounding_execution_context_consumption_decision import (
    GroundingExecutionContextConsumptionDecision,
)
from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_context_consumption_decision_result_normalizer import (
    GroundingExecutionContextConsumptionDecisionResultNormalizer,
)
from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


class GroundingExecutionContextConsumptionDecisionEvaluator:
    """Derive and normalize the canonical decision result."""

    @staticmethod
    def evaluate(
        consumption: GroundingExecutionContextConsumptionResult,
    ) -> GroundingExecutionContextConsumptionDecisionResult:
        decision = GroundingExecutionContextConsumptionDecision.from_consumption(consumption)
        raw_result = GroundingExecutionContextConsumptionDecisionResult.from_decision(decision)
        return GroundingExecutionContextConsumptionDecisionResultNormalizer.normalize(raw_result)


__all__ = ["GroundingExecutionContextConsumptionDecisionEvaluator"]
