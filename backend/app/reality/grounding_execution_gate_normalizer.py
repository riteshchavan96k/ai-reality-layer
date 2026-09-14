from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_gate import GroundingExecutionGateResult


class GroundingExecutionGateResultNormalizer:
    """Normalize typed or legacy grounding execution-gate results."""

    @staticmethod
    def normalize(raw_result: object) -> GroundingExecutionGateResult:
        if isinstance(raw_result, GroundingExecutionGateResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingExecutionGateResult(
                status=values["status"],
                grounding_status=values["grounding_status"],
                allowed=values["allowed"],
                reason=values.get("reason"),
                gate_evaluated=values.get("gate_evaluated", True),
            )

        raise ValueError(
            "grounding execution gate result must be a result contract or mapping"
        )


__all__ = ["GroundingExecutionGateResultNormalizer"]
