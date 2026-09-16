from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_authorization_consumption_result import (
    GroundingExecutionAuthorizationConsumptionResult,
)


class GroundingExecutionAuthorizationConsumptionResultNormalizer:
    """Normalize typed or legacy grounding execution-authorization consumption results."""

    @staticmethod
    def normalize(raw_result: object) -> GroundingExecutionAuthorizationConsumptionResult:
        if isinstance(raw_result, GroundingExecutionAuthorizationConsumptionResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingExecutionAuthorizationConsumptionResult(
                status=values["status"],
                authorization_status=values["authorization_status"],
                usable=values["usable"],
                reason=values.get("reason"),
                consumption_executed=values.get("consumption_executed", True),
            )

        raise ValueError(
            "grounding execution authorization consumption result must be a result contract or mapping"
        )


__all__ = ["GroundingExecutionAuthorizationConsumptionResultNormalizer"]
