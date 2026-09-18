from typing import Any

from backend.app.reality.claim_evidence_linking import ClaimEvidenceLink, ClaimEvidenceLinkingResult
from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim


class ClaimEvidenceLinker:
    """Create explicit provenance links between extracted claims and known evidence sources."""

    def link_result(self, claim_result: ClaimExtractionResult | dict[str, Any], evidence: dict[str, Any]) -> ClaimEvidenceLinkingResult:
        if isinstance(claim_result, dict):
            claim_result = self._claim_result_from_mapping(claim_result)
        if not isinstance(claim_result, ClaimExtractionResult):
            raise ValueError("claim_result must be a ClaimExtractionResult")
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")

        sources = evidence.get("sources", [])
        if not isinstance(sources, list):
            raise ValueError("evidence sources must be a list")
        source_refs: list[str] = []
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("each evidence source must be a dictionary")
            uri = source.get("uri")
            if uri is not None and str(uri).strip():
                source_refs.append(str(uri).strip())
        known_refs = set(source_refs)
        claim_count = len(claim_result.claims)

        if claim_result.status == "unavailable":
            return ClaimEvidenceLinkingResult.unavailable_result(claim_result.reason or "claim_extraction_unavailable", claim_count=claim_count, source_count=len(sources))
        if claim_result.status == "empty":
            return ClaimEvidenceLinkingResult.empty_result(claim_count=claim_count, source_count=len(sources))
        if not known_refs:
            return ClaimEvidenceLinkingResult.empty_result(claim_count=claim_count, source_count=len(sources))

        links: list[ClaimEvidenceLink] = []
        seen: set[tuple[str, str]] = set()
        for claim in claim_result.claims:
            for source_ref in claim.source_refs:
                normalized_ref = source_ref.strip()
                if normalized_ref not in known_refs:
                    continue
                key = (claim.text.casefold(), normalized_ref)
                if key in seen:
                    continue
                seen.add(key)
                links.append(ClaimEvidenceLink(claim_text=claim.text, source_ref=normalized_ref))

        if not links:
            return ClaimEvidenceLinkingResult.empty_result(claim_count=claim_count, source_count=len(sources))
        return ClaimEvidenceLinkingResult.usable_result(tuple(links), claim_count=claim_count, source_count=len(sources))

    def link(self, claim_result: ClaimExtractionResult | dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        """Preserve a dictionary API while returning the canonical linking result."""
        return self.link_result(claim_result, evidence).to_dict()

    @staticmethod
    def _claim_result_from_mapping(value: dict[str, Any]) -> ClaimExtractionResult:
        status = value.get("status")
        raw_claims = value.get("claims", [])
        if not isinstance(raw_claims, list):
            raise ValueError("claim_result claims must be a list")
        claims: list[EvidenceClaim] = []
        for raw_claim in raw_claims:
            if not isinstance(raw_claim, dict):
                raise ValueError("each claim must be a dictionary")
            source_refs = raw_claim.get("source_refs", [])
            if not isinstance(source_refs, list):
                raise ValueError("claim source_refs must be a list")
            claims.append(EvidenceClaim(text=raw_claim.get("text", ""), source_refs=tuple(source_refs), extraction_method=raw_claim.get("extraction_method", "deterministic_sentence_split")))
        return ClaimExtractionResult(status=status, claims=tuple(claims), source_count=value.get("source_count", 0), extraction_executed=value.get("extraction_executed", True), reason=value.get("reason"))


__all__ = ["ClaimEvidenceLinker"]