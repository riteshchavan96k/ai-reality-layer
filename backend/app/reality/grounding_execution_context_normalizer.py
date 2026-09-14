from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_execution_context import GroundingExecutionContext


class GroundingExecutionContextNormalizer:
    """Normalize typed or legacy execution contexts into one canonical contract."""

    @staticmethod
    def normalize(raw_context: object) -> GroundingExecutionContext:
        if isinstance(raw_context, GroundingExecutionContext):
            return raw_context

        if isinstance(raw_context, Mapping):
            values: dict[str, Any] = dict(raw_context)
            sources = values.get("sources", [])
            if not isinstance(sources, list):
                raise ValueError("grounding execution context sources must be a list")
            if not all(isinstance(source, dict) for source in sources):
                raise ValueError("grounding execution context sources must be dictionaries")

            return GroundingExecutionContext(
                task=values["task"],
                grounding_status=values["grounding_status"],
                content=values.get("content"),
                sources=[dict(source) for source in sources],
                source_count=values["source_count"],
                execution_allowed=values.get("execution_allowed", True),
                context_prepared=values.get("context_prepared", True),
            )

        raise ValueError(
            "grounding execution context must be a result contract or mapping"
        )


__all__ = ["GroundingExecutionContextNormalizer"]
