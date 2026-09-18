from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision,
)


class GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator:
    """Derive the final execution decision from the canonical consumed result."""

    @staticmethod
    def evaluate(
        consumption_result: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
    ) -> GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision:
        return GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision.from_consumption_result(
            consumption_result
        )


__all__ = [
    "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator",
]
