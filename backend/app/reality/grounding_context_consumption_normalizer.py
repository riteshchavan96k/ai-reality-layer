from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_context_consumption_result import GroundingContextConsumptionResult


class GroundingContextConsumptionResultNormalizer:
    """Normalize typed or legacy grounding-consumption results."""

    @staticmethod
    def normalize(raw_result: object) -> GroundingContextConsumptionResult:
        if isinstance(raw_result, GroundingContextConsumptionResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingContextConsumptionResult(
                status=values["status"],
                grounding_status=values["grounding_status"],
                usable=values["usable"],
                reason=values.get("reason"),
                consumption_executed=values.get("consumption_executed", True),
            )

        raise ValueError(
            "grounding context consumption result must be a result contract or mapping"
        )


__all__ = ["GroundingContextConsumptionResultNormalizer"]
