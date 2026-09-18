from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_authorization_consumption_decision_result_consumption_result_decision_result import (
    GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult,
)


class GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer:
    """Normalize typed or mapping final authorization-consumption decision results."""

    @staticmethod
    def normalize(
        raw_result: object,
    ) -> GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult:
        if isinstance(
            raw_result,
            GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult,
        ):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResult(
                status=values["status"],
                authorization_status=values["authorization_status"],
                allowed=values["allowed"],
                reason=values.get("reason"),
                decision_executed=values.get("decision_executed", True),
            )

        raise ValueError(
            "grounding execution authorization consumption decision result consumption result decision result "
            "must be a result contract or mapping"
        )


__all__ = [
    "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultNormalizer",
]
