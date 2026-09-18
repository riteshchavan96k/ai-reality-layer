from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result_consumption_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult,
)


class GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer:
    """Normalize typed or mapping final authorization-consumption result states."""

    @staticmethod
    def normalize(
        raw_result: object,
    ) -> GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult:
        if isinstance(
            raw_result,
            GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult,
        ):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult(
                status=values["status"],
                authorization_status=values["authorization_status"],
                allowed=values["allowed"],
                reason=values.get("reason"),
                decision_executed=values.get("decision_executed", True),
                consumption_executed=values.get("consumption_executed", True),
            )

        raise ValueError(
            "grounding execution authorization consumption decision result consumption result "
            "decision result consumption result must be a result contract or mapping"
        )


__all__ = [
    "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResultNormalizer",
]
