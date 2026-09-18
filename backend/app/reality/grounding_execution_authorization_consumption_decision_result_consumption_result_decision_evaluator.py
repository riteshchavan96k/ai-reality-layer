from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult,
)


class GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator:
    """Derive the canonical result from the final authorization-consumption execution decision."""

    @staticmethod
    def evaluate(
        consumption_result: GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResult,
    ) -> GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult:
        decision = GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecision.from_consumption_result(
            consumption_result
        )
        return GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult.from_decision(
            decision
        )


__all__ = [
    "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionEvaluator",
]
