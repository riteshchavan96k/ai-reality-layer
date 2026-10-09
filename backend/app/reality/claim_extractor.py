import re
from typing import Any

from backend.app.reality.claim_extraction import ClaimExtractionResult, EvidenceClaim
from backend.app.reality.claim_semantic_structurer import (
    ClaimSemanticStructurer,
    ClaimSemanticStructuringStage,
)
from backend.app.reality.claim_extraction_normalizer import ClaimExtractionResultNormalizer
from backend.app.reality.retrieval_input_bounds import MAX_RETRIEVED_CLAIMS


class EvidenceClaimExtractor:
    """Extract deterministic candidate claims from normalized evidence content."""

    _SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

    def __init__(
        self, semantic_structurer: ClaimSemanticStructurer | None = None
    ) -> None:
        # The legacy usable/no-adapter path deliberately permits more than
        # the retrieval claim budget. A configured semantic adapter must not
        # inherit that unbounded invocation count.
        self._semantic_adapter_configured = semantic_structurer is not None
        self._semantic_structuring = ClaimSemanticStructuringStage(
            semantic_structurer
        )

    def extract_result(self, evidence: dict[str, Any]) -> ClaimExtractionResult:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dictionary")
        sources = evidence.get("sources", [])
        if evidence.get("status") not in {"usable", "completed"}:
            return self._unavailable(
                evidence.get("reason") or "evidence_not_usable",
                len(sources) if isinstance(sources, list) else 0,
            )
        if not isinstance(sources, list):
            raise ValueError("evidence sources must be a list")
        if any(not isinstance(source, dict) for source in sources):
            raise ValueError("each evidence source must be a dictionary")

        content = evidence.get("content")
        if content is not None and not isinstance(content, str):
            raise ValueError("evidence content must be a string or None")
        source_count = len(sources)

        # A source-less payload cannot establish claim provenance, even when
        # it contains text. Do not invent a source reference.
        if not sources:
            if content and content.strip():
                return self._unavailable("missing_source_attribution", 0)
            return ClaimExtractionResultNormalizer.normalize(
                ClaimExtractionResult.empty_result()
            )

        raw_uris = [source.get("uri") for source in sources]
        if any(not isinstance(uri, str) or not uri.strip() for uri in raw_uris):
            return self._unavailable("missing_source_attribution", source_count)
        # Treat whitespace-padded aliases as one source identity before
        # constructing claims or passing references to semantic adapters.
        uris = [uri.strip() for uri in raw_uris]
        if len(set(uris)) != source_count:
            return self._unavailable("duplicate_source_attribution", source_count)

        scoped = ["content" in source for source in sources]
        if any(scoped):
            if not all(scoped):
                return self._unavailable("incomplete_source_scoped_content", source_count)
            if any(
                not isinstance(source["content"], str)
                or not source["content"].strip()
                for source in sources
            ):
                return self._unavailable("invalid_source_scoped_content", source_count)
            combined = "\n\n".join(source["content"].strip() for source in sources)
            if content is not None and content.strip() != combined:
                return self._unavailable("inconsistent_source_scoped_content", source_count)
            segments = [
                (source["content"], (uri,))
                for source, uri in zip(sources, uris)
            ]
        elif source_count == 1:
            if not content or not content.strip():
                return ClaimExtractionResultNormalizer.normalize(
                    ClaimExtractionResult.empty_result(source_count=1)
                )
            # A single URI is unambiguous and remains backward compatible.
            segments = [(content, (uris[0],))]
        else:
            if not content or not content.strip():
                return ClaimExtractionResultNormalizer.normalize(
                    ClaimExtractionResult.empty_result(source_count=source_count)
                )
            # A combined text body cannot establish which source said what.
            return self._unavailable("ambiguous_source_attribution", source_count)

        claims_by_key: dict[str, EvidenceClaim] = {}
        for source_text, source_refs in segments:
            for raw_sentence in self._SENTENCE_SPLIT.split(source_text):
                sentence = " ".join(raw_sentence.split()).strip()
                if not sentence:
                    continue
                key = sentence.casefold()
                previous = claims_by_key.get(key)
                if previous is None:
                    # Enforce the retrieved claim budget as before. The
                    # legacy usable/no-adapter extractor remains compatible,
                    # but optional inference must never bypass the same cap
                    # when callers supply status="usable" directly.
                    # Check before *any* adapter calls or partial claim output.
                    if (
                        (
                            evidence.get("status") == "completed"
                            or self._semantic_adapter_configured
                        )
                        and len(claims_by_key) >= MAX_RETRIEVED_CLAIMS
                    ):
                        return self._unavailable(
                            "retrieved_claim_limit_exceeded", source_count,
                        )
                    claims_by_key[key] = EvidenceClaim(
                        text=sentence, source_refs=source_refs
                    )
                else:
                    claims_by_key[key] = EvidenceClaim(
                        text=previous.text,
                        source_refs=tuple(
                            dict.fromkeys((*previous.source_refs, *source_refs))
                        ),
                        extraction_method=previous.extraction_method,
                        semantic_structure=previous.semantic_structure,
                    )

        if not claims_by_key:
            return ClaimExtractionResultNormalizer.normalize(
                ClaimExtractionResult.empty_result(source_count=source_count)
            )
        # Structure only after deduplication, so the optional adapter sees the
        # complete source lineage and is invoked once per distinct claim.
        claims = tuple(
            EvidenceClaim(
                text=claim.text,
                source_refs=claim.source_refs,
                extraction_method=claim.extraction_method,
                semantic_structure=self._semantic_structuring.structure_claim(
                    claim.text, claim.source_refs
                ),
            )
            for claim in claims_by_key.values()
        )
        return ClaimExtractionResultNormalizer.normalize(
            ClaimExtractionResult.usable_result(claims, source_count=source_count)
        )

    @staticmethod
    def _unavailable(reason: str, source_count: int) -> ClaimExtractionResult:
        return ClaimExtractionResultNormalizer.normalize(
            ClaimExtractionResult.unavailable_result(reason, source_count)
        )

    def extract(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Preserve a dictionary API while returning the canonical extraction result."""
        return self.extract_result(evidence).to_dict()


__all__ = ["EvidenceClaimExtractor"]
