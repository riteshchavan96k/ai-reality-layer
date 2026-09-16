from backend.app.reality.grounding_execution_authorization_consumption_decision import (
    GroundingExecutionAuthorizationConsumptionDecision,
)
from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)


class GroundingExecutionAuthorizationConsumptionDecisionEvaluator:
    """Derive the canonical execution decision from authorization consumption."""

    @staticmethod
    def evaluate(
        consumption: GroundingExecutionAuthorizationConsumptionResult,
    ) -> GroundingExecutionAuthorizationConsumptionDecision:
        return GroundingExecutionAuthorizationConsumptionDecision.from_consumption(
            consumption
        )


__all__ = ["GroundingExecutionAuthorizationConsumptionDecisionEvaluator"]
