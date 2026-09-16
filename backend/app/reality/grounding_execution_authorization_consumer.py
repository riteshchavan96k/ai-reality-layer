from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)
from backend.app.reality.grounding_execution_authorization_result import (
    GroundingExecutionAuthorizationResult,
)


class GroundingExecutionAuthorizationConsumer:
    """Consume canonical execution-authorization results before model execution."""

    @staticmethod
    def consume(
        result: GroundingExecutionAuthorizationResult,
    ) -> GroundingExecutionAuthorizationConsumptionResult:
        if not isinstance(result, GroundingExecutionAuthorizationResult):
            raise ValueError(
                "authorization result must be a GroundingExecutionAuthorizationResult"
            )

        if result.authorized:
            return GroundingExecutionAuthorizationConsumptionResult.usable_result(
                authorization_status=result.status,
                consumption_executed=True,
            )

        return GroundingExecutionAuthorizationConsumptionResult.rejected_result(
            authorization_status=result.status,
            reason=result.reason or "execution_authorization_denied",
            consumption_executed=True,
        )


__all__ = ["GroundingExecutionAuthorizationConsumer"]
