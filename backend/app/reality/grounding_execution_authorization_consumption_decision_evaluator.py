from backend.app.reality.grounding_execution_authorization_consumption_decision import (
    GroundingExecutionAuthorizationConsumptionDecision,
)
from backend.app.reality.grounding_execution_authorization_consumption_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResult,
)
from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)


class GroundingExecutionAuthorizationConsumptionDecisionEvaluator:
    """Derive the canonical execution decision result from authorization consumption."""

    @staticmethod
    def evaluate(
        consumption: GroundingExecutionAuthorizationConsumptionResult,
    ) -> GroundingExecutionAuthorizationConsumptionDecisionResult:
        decision = GroundingExecutionAuthorizationConsumptionDecision.from_consumption(
            consumption
        )
        return GroundingExecutionAuthorizationConsumptionDecisionResult.from_decision(
            decision
        )


__all__ = ["GroundingExecutionAuthorizationConsumptionDecisionEvaluator"]
