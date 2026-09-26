from typing import Any
import re

from backend.app.reality.claim_conflict import ClaimConflict, ClaimConflictResult
from backend.app.reality.claim_conflict_normalizer import ClaimConflictResultNormalizer
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim


class ClaimConflictDetector:
    """Detect only explicit deterministic negation pairs; never infer semantic disagreement."""

    _NEGATION = re.compile(r"^(not|no|never)\s+(.*)$", re.IGNORECASE)

    def detect_result(self, claim_result: ClaimExtractionResult | dict[str, Any]) -> ClaimConflictResult:
        if isinstance(claim_result, dict):
            claim_result = self._from_mapping(claim_result)
        if not isinstance(claim_result, ClaimExtractionResult):
            raise ValueError("claim_result must be a ClaimExtractionResult")
        if claim_result.status == "unavailable":
            return ClaimConflictResultNormalizer.normalize(
                ClaimConflictResult.unavailable_result(
                    claim_result.reason or "claim_extraction_unavailable",
                    len(claim_result.claims),
                )
            )
        if claim_result.status == "empty":
            return ClaimConflictResultNormalizer.normalize(ClaimConflictResult.empty_result(0))

        claims = list(claim_result.claims)
        normalized: dict[str, list[EvidenceClaim]] = {}
        for claim in claims:
            key = self._positive_form(claim.text)
            normalized.setdefault(key, []).append(claim)

        conflicts: list[ClaimConflict] = []
        seen: set[tuple[str, str]] = set()
        for items in normalized.values():
            positives = [c for c in items if not self._is_negated(c.text)]
            negatives = [c for c in items if self._is_negated(c.text)]
            for positive in positives:
                for negative in negatives:
                    key = tuple(sorted((positive.text.casefold(), negative.text.casefold())))
                    if key in seen:
                        continue
                    seen.add(key)
                    conflicts.append(ClaimConflict(positive.text, negative.text, positive.source_refs, negative.source_refs))
        if not conflicts:
            return ClaimConflictResultNormalizer.normalize(ClaimConflictResult.empty_result(len(claims)))
        return ClaimConflictResultNormalizer.normalize(
            ClaimConflictResult.usable_result(tuple(conflicts), len(claims))
        )

    def detect(self, claim_result: ClaimExtractionResult | dict[str, Any]) -> dict[str, Any]:
        """Preserve the dictionary API while returning the canonical conflict result."""
        return self.detect_result(claim_result).to_dict()

    @classmethod
    def _is_negated(cls, text: str) -> bool:
        return bool(cls._NEGATION.match(" ".join(text.split())))

    @classmethod
    def _positive_form(cls, text: str) -> str:
        normalized = " ".join(text.split()).casefold().strip()
        match = cls._NEGATION.match(normalized)
        return match.group(2).strip() if match else normalized

    @staticmethod
    def _from_mapping(value: dict[str, Any]) -> ClaimExtractionResult:
        raw_claims = value.get("claims", [])
        if not isinstance(raw_claims, list):
            raise ValueError("claim_result claims must be a list")
        claims = []
        for item in raw_claims:
            if not isinstance(item, dict):
                raise ValueError("each claim must be a dictionary")
            refs = item.get("source_refs", [])
            if not isinstance(refs, list):
                raise ValueError("claim source_refs must be a list")
            claims.append(EvidenceClaim(item.get("text", ""), tuple(refs), item.get("extraction_method", "deterministic_sentence_split")))
        return ClaimExtractionResult(value.get("status"), tuple(claims), value.get("source_count", 0), value.get("extraction_executed", True), value.get("reason"))


__all__ = ["ClaimConflictDetector"]
