from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_authorization_result import (
    GroundingExecutionAuthorizationResult,
)


class GroundingExecutionAuthorizationResultNormalizer:
    """Normalize typed or legacy execution-authorization results."""

    @staticmethod
    def normalize(raw_result: object) -> GroundingExecutionAuthorizationResult:
        if isinstance(raw_result, GroundingExecutionAuthorizationResult):
            return raw_result

        if isinstance(raw_result, Mapping):
            values: dict[str, Any] = dict(raw_result)
            return GroundingExecutionAuthorizationResult(
                status=values["status"],
                grounding_status=values["grounding_status"],
                authorized=values["authorized"],
                reason=values.get("reason"),
                authorization_executed=values.get("authorization_executed", True),
            )

        raise ValueError(
            "grounding execution authorization result must be a result contract or mapping"
        )


__all__ = ["GroundingExecutionAuthorizationResultNormalizer"]
