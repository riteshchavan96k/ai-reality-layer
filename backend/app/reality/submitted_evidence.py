from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from backend.app.reality.claim_extraction import (
    ClaimExtractionResult,
    EvidenceClaim,
)
from backend.app.reality.claim_extractor import EvidenceClaimExtractor


MAX_SUBMITTED_DOCUMENTS = 20
MAX_SUBMITTED_CONTENT_CHARS = 50_000
MAX_SUBMITTED_URI_CHARS = 2_048
MAX_SUBMITTED_TITLE_CHARS = 500


@dataclass(frozen=True)
class SubmittedEvidenceDocument:
    """One source-scoped evidence document supplied by an API caller."""

    content: str
    uri: str
    title: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("submitted evidence content must be non-empty")
        if len(self.content) > MAX_SUBMITTED_CONTENT_CHARS:
            raise ValueError("submitted evidence content is too large")

        if not isinstance(self.uri, str) or not self.uri.strip():
            raise ValueError("submitted evidence uri must be non-empty")
        normalized_uri = self.uri.strip()
        if len(normalized_uri) > MAX_SUBMITTED_URI_CHARS:
            raise ValueError("submitted evidence uri is too long")
        parsed = urlparse(normalized_uri)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "submitted evidence uri must use http or https"
            )
        object.__setattr__(self, "uri", normalized_uri)

        if self.title is not None:
            if not isinstance(self.title, str) or not self.title.strip():
                raise ValueError(
                    "submitted evidence title must be non-empty when provided"
                )
            normalized_title = self.title.strip()
            if len(normalized_title) > MAX_SUBMITTED_TITLE_CHARS:
                raise ValueError("submitted evidence title is too long")
            object.__setattr__(self, "title", normalized_title)

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "SubmittedEvidenceDocument":
        if not isinstance(value, Mapping):
            raise ValueError("submitted evidence document must be a mapping")
        return cls(
            content=value.get("content", ""),
            uri=value.get("uri", ""),
            title=value.get("title"),
        )

    def source_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "uri": self.uri,
        }


@dataclass(frozen=True)
class SubmittedEvidenceBundle:
    """Validated source-scoped evidence supplied directly by a developer."""

    documents: tuple[SubmittedEvidenceDocument, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.documents, tuple):
            raise ValueError("submitted evidence documents must be a tuple")
        if not self.documents:
            raise ValueError("at least one submitted evidence document is required")
        if len(self.documents) > MAX_SUBMITTED_DOCUMENTS:
            raise ValueError("too many submitted evidence documents")
        if any(
            not isinstance(document, SubmittedEvidenceDocument)
            for document in self.documents
        ):
            raise ValueError(
                "documents must contain SubmittedEvidenceDocument values"
            )

        uris = [document.uri for document in self.documents]
        if len(set(uris)) != len(uris):
            raise ValueError("submitted evidence source uris must be unique")

    @classmethod
    def from_mappings(
        cls,
        documents: Iterable[Mapping[str, Any]],
    ) -> "SubmittedEvidenceBundle":
        if isinstance(documents, (str, bytes, Mapping)):
            raise ValueError(
                "submitted evidence documents must be an iterable of mappings"
            )
        try:
            normalized = tuple(
                SubmittedEvidenceDocument.from_mapping(document)
                for document in documents
            )
        except TypeError as exc:
            raise ValueError(
                "submitted evidence documents must be iterable"
            ) from exc
        return cls(normalized)

    def to_evidence(self) -> dict[str, Any]:
        """Build canonical completed evidence without claiming system retrieval."""
        content = "\n\n".join(
            document.content.strip()
            for document in self.documents
        )
        sources = [
            document.source_dict()
            for document in self.documents
        ]
        return {
            "status": "completed",
            "sources": sources,
            "content": content,
            "source_count": len(sources),
            "has_content": True,
            "normalization_executed": True,
        }

    def extract_claims(
        self,
        extractor: EvidenceClaimExtractor,
    ) -> ClaimExtractionResult:
        """Extract per-source claims, merging exact duplicates across sources."""
        if not isinstance(extractor, EvidenceClaimExtractor):
            raise ValueError("extractor must be an EvidenceClaimExtractor")

        claims_by_key: dict[str, EvidenceClaim] = {}
        ordered_keys: list[str] = []

        for document in self.documents:
            result = extractor.extract_result(
                {
                    "status": "completed",
                    "sources": [document.source_dict()],
                    "content": document.content,
                }
            )
            if result.status == "unavailable":
                return ClaimExtractionResult.unavailable_result(
                    result.reason or "claim_extraction_unavailable",
                    source_count=len(self.documents),
                )

            for claim in result.claims:
                key = claim.text.casefold()
                existing = claims_by_key.get(key)
                if existing is None:
                    claims_by_key[key] = claim
                    ordered_keys.append(key)
                    continue

                merged_refs = tuple(
                    dict.fromkeys(
                        (*existing.source_refs, *claim.source_refs)
                    )
                )
                claims_by_key[key] = EvidenceClaim(
                    text=existing.text,
                    source_refs=merged_refs,
                    extraction_method=existing.extraction_method,
                )

        claims = tuple(
            claims_by_key[key]
            for key in ordered_keys
        )
        if not claims:
            return ClaimExtractionResult.empty_result(
                source_count=len(self.documents)
            )
        return ClaimExtractionResult.usable_result(
            claims,
            source_count=len(self.documents),
        )


__all__ = [
    "MAX_SUBMITTED_CONTENT_CHARS",
    "MAX_SUBMITTED_DOCUMENTS",
    "MAX_SUBMITTED_TITLE_CHARS",
    "MAX_SUBMITTED_URI_CHARS",
    "SubmittedEvidenceBundle",
    "SubmittedEvidenceDocument",
]
