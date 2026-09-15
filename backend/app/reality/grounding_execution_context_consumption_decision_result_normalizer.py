from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_context_consumption_decision_result import (
    GroundingExecutionContextConsumptionDecisionResult,
)


class GroundingExecutionContextConsumptionDecisionResultNormalizer:
    """Normalize typed or legacy execution-context decision results."""

    @staticmethod
    def normalize(
        raw_result: object,
    ) -> GroundingExecutionContextConsumptionDecisionResult:
        if isinstance(raw_result, GroundingExecutionContextConsumptionDecisionResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingExecutionContextConsumptionDecisionResult(
                status=values["status"],
                grounding_status=values["grounding_status"],
                allowed=values["allowed"],
                reason=values.get("reason"),
                decision_executed=values.get("decision_executed", True),
            )

        raise ValueError(
            "grounding execution context consumption decision result must be a result contract or mapping"
        )


__all__ = ["GroundingExecutionContextConsumptionDecisionResultNormalizer"]
