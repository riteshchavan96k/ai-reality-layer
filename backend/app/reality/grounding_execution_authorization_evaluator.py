from backend.app.reality.grounding_execution_authorization import GroundingExecutionAuthorization
from backend.app.reality.grounding_execution_authorization_result import GroundingExecutionAuthorizationResult
from backend.app.reality.grounding_execution_authorization_result_normalizer import (
    GroundingExecutionAuthorizationResultNormalizer,
)
from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)


class GroundingExecutionAuthorizationEvaluator:
    """Derive and canonicalize execution authorization from the decision result."""

    @staticmethod
    def evaluate(
        decision_result: GroundingExecutionContextConsumptionDecisionResult,
    ) -> GroundingExecutionAuthorizationResult:
        if not isinstance(
            decision_result,
            GroundingExecutionContextConsumptionDecisionResult,
        ):
            raise ValueError(
                "decision_result must be a GroundingExecutionContextConsumptionDecisionResult"
            )
        authorization = GroundingExecutionAuthorization.from_decision_result(decision_result)
        raw_result = GroundingExecutionAuthorizationResult.from_authorization(authorization)
        return GroundingExecutionAuthorizationResultNormalizer.normalize(raw_result)


__all__ = ["GroundingExecutionAuthorizationEvaluator"]
