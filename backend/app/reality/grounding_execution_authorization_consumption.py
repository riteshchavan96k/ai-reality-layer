from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)


# Backward-compatible name retained for existing callers and Step 110 tests.
GroundingExecutionAuthorizationConsumption = GroundingExecutionAuthorizationConsumptionResult


__all__ = [
    "GroundingExecutionAuthorizationConsumption",
    "GroundingExecutionAuthorizationConsumptionResult",
]
