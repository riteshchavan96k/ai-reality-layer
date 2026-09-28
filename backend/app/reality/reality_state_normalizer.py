from collections.abc import Mapping

from backend.app.reality.reality_state import RealityState


class RealityStateNormalizer:
    """Normalize typed or mapping-shaped Reality State values."""

    @staticmethod
    def normalize(raw_state: object) -> RealityState:
        if isinstance(raw_state, RealityState):
            return raw_state
        if isinstance(raw_state, Mapping):
            return RealityState.validate(dict(raw_state))
        raise ValueError("reality state must be a RealityState or mapping")


__all__ = ["RealityStateNormalizer"]
