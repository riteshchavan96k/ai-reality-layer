import re
from typing import Any

from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.claim_extraction_normalizer import ClaimExtractionResultNormalizer


class EvidenceClaimExtractor:
    """Extract deterministic candidate claims from normalized evidence content."""

    _SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

    def extract_result(self, evidence: dict[str, Any]) -> ClaimExtractionResult:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")
        if evidence.get("status") != "usable":
            return ClaimExtractionResultNormalizer.normalize(
                ClaimExtractionResult.unavailable_result(
                    evidence.get("reason") or "evidence_not_usable",
                    source_count=len(evidence.get("sources", [])) if isinstance(evidence.get("sources", []), list) else 0,
                )
            )

        content = evidence.get("content")
        sources = evidence.get("sources", [])
        if content is None or not isinstance(content, str) or not content.strip():
            return ClaimExtractionResultNormalizer.normalize(
                ClaimExtractionResult.empty_result(source_count=len(sources))
            )
        if not isinstance(sources, list):
            raise ValueError("evidence sources must be a list")

        source_refs: list[str] = []
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each evidence source must be a dictionary")
            uri = source.get("uri")
            if uri is not None and str(uri).strip():
                source_refs.append(str(uri).strip())

        claims: list[EvidenceClaim] = []
        seen: set[str] = set()
        for raw_sentence in self._SENTENCE_SPLIT.split(content):
            sentence = " ".join(raw_sentence.split()).strip()
            if not sentence:
                continue
            normalized_key = sentence.casefold()
            if normalized_key in seen:
                continue
            seen.add(normalized_key)
            claims.append(EvidenceClaim(text=sentence, source_refs=tuple(source_refs)))

        if not claims:
            return ClaimExtractionResultNormalizer.normalize(
                ClaimExtractionResult.empty_result(source_count=len(sources))
            )
        return ClaimExtractionResultNormalizer.normalize(
            ClaimExtractionResult.usable_result(tuple(claims), source_count=len(sources))
        )

    def extract(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Preserve a dictionary API while returning the canonical extraction result."""
        return self.extract_result(evidence).to_dict()


__all__ = ["EvidenceClaimExtractor"]
