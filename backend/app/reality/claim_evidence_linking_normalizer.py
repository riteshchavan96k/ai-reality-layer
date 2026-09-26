from collections.abc import Mapping

from backend.app.reality.claim_evidence_linking import ClaimEvidenceLinkingResult


class ClaimEvidenceLinkingResultNormalizer:
    """Normalize typed or mapping-shaped claim-evidence linking results."""

    @staticmethod
    def normalize(raw_result: object) -> ClaimEvidenceLinkingResult:
        if isinstance(raw_result, ClaimEvidenceLinkingResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return ClaimEvidenceLinkingResult.validate(dict(raw_result))
        raise ValueError(
            "claim-evidence linking result must be a claim-evidence linking contract or mapping"
        )


__all__ = ["ClaimEvidenceLinkingResultNormalizer"]
