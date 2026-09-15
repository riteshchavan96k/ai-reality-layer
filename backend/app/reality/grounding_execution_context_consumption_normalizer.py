from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_context_consumption_result import (
    GroundingExecutionContextConsumptionResult,
)


class GroundingExecutionContextConsumptionResultNormalizer:
    """Normalize typed or legacy execution-context consumption results."""

    @staticmethod
    def normalize(raw_result: object) -> GroundingExecutionContextConsumptionResult:
        if isinstance(raw_result, GroundingExecutionContextConsumptionResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingExecutionContextConsumptionResult(
                status=values["status"],
                grounding_status=values["grounding_status"],
                usable=values["usable"],
                reason=values.get("reason"),
                consumption_executed=values.get("consumption_executed", True),
            )

        raise ValueError(
            "grounding execution context consumption result must be a result contract or mapping"
        )


__all__ = ["GroundingExecutionContextConsumptionResultNormalizer"]
