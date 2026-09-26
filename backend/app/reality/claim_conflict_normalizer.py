from collections.abc import Mapping

from backend.app.reality.claim_conflict import ClaimConflictResult


class ClaimConflictResultNormalizer:
    """Normalize typed or mapping-shaped claim-conflict results."""

    @staticmethod
    def normalize(raw_result: object) -> ClaimConflictResult:
        if isinstance(raw_result, ClaimConflictResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return ClaimConflictResult.validate(dict(raw_result))
        raise ValueError(
            "claim conflict result must be a claim-conflict contract or mapping"
        )


__all__ = ["ClaimConflictResultNormalizer"]
