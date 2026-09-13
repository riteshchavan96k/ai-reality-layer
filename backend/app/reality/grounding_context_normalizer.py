from collections.abc import Mapping
from typing import Any

from backend.app.reality.grounding_context_contract import GroundingContext


class GroundingContextNormalizer:
    """Normalize typed or legacy grounding contexts into one canonical contract."""

    @staticmethod
    def normalize(raw_context: object) -> GroundingContext:
        if isinstance(raw_context, GroundingContext):
            return raw_context

        if isinstance(raw_context, Mapping):
            values: dict[str, Any] = dict(raw_context)
            sources = values.get("sources", [])
            if not isinstance(sources, list):
                raise ValueError("grounding context sources must be a list")
            if not all(isinstance(source, dict) for source in sources):
                raise ValueError("grounding context sources must be dictionaries")

            return GroundingContext(
                status=values["status"],
                task=values["task"],
                content=values.get("content"),
                sources=[dict(source) for source in sources],
                source_count=values["source_count"],
                grounding_executed=values.get("grounding_executed", True),
            )

        raise ValueError("grounding context must be a result contract or mapping")


__all__ = ["GroundingContextNormalizer"]
