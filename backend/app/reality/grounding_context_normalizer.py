from collections.abc import Mapping

from backend.app.reality.grounding_context_contract import GroundingContext


class GroundingContextNormalizer:
    """Normalize typed or legacy grounding contexts into one canonical contract."""

    @staticmethod
    def normalize(raw_context: object) -> GroundingContext:
        if isinstance(raw_context, GroundingContext):
            return GroundingContext.validate(raw_context)

        if isinstance(raw_context, Mapping):
            values = dict(raw_context)
            values.setdefault("grounding_executed", True)
            return GroundingContext.validate(values)

        raise ValueError("grounding context must be a result contract or mapping")


__all__ = ["GroundingContextNormalizer"]
