from collections.abc import Mapping

from backend.app.reality.grounded_result import GroundedResultEnvelope


class GroundedResultEnvelopeNormalizer:
    """Normalize typed or mapping-shaped grounded-result envelopes."""

    @staticmethod
    def normalize(raw_result: object) -> GroundedResultEnvelope:
        if isinstance(raw_result, GroundedResultEnvelope):
            return raw_result
        if isinstance(raw_result, Mapping):
            return GroundedResultEnvelope.validate(dict(raw_result))
        raise ValueError("grounded result must be a GroundedResultEnvelope or mapping")


__all__ = ["GroundedResultEnvelopeNormalizer"]
