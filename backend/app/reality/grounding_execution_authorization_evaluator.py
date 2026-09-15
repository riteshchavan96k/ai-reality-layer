from backend.app.reality.grounding_execution_authorization import GroundingExecutionAuthorization
from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)


class GroundingExecutionAuthorizationEvaluator:
    """Derive the final execution authorization from the canonical decision result."""

    @staticmethod
    def evaluate(
        decision_result: GroundingExecutionContextConsumptionDecisionResult,
    ) -> GroundingExecutionAuthorization:
        if not isinstance(
            decision_result,
            GroundingExecutionContextConsumptionDecisionResult,
        ):
            raise ValueError(
                "decision_result must be a GroundingExecutionContextConsumptionDecisionResult"
            )
        return GroundingExecutionAuthorization.from_decision_result(decision_result)


__all__ = ["GroundingExecutionAuthorizationEvaluator"]
