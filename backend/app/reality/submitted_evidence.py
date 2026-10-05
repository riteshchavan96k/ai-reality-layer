from dataclasses import dataclass
from itertools import islice
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlparse

from backend.app.reality.claim_extraction import (
    ClaimExtractionResult,
    EvidenceClaim,
)
from backend.app.reality.claim_extractor import EvidenceClaimExtractor
from backend.app.reality.retrieval_input_bounds import MAX_RETRIEVED_CLAIMS
from backend.app.reality.freshness_policy import is_positive_finite_number
from backend.app.reality.source_observation import (
    SourceObservation,
    SourceObservationResult,
)
from backend.app.reality.source_provenance import SourceProvenanceResult


MAX_SUBMITTED_DOCUMENTS = 20
MAX_SUBMITTED_CONTENT_CHARS = 50_000
MAX_SUBMITTED_URI_CHARS = 2_048
MAX_SUBMITTED_TITLE_CHARS = 500
# Keep submitted and retrieved graph amplification budgets aligned.
MAX_SUBMITTED_CLAIMS = MAX_RETRIEVED_CLAIMS


@dataclass(frozen=True)
class SubmittedEvidenceDocument:
    """One source-scoped evidence document supplied by an API caller."""

    content: str
    uri: str
    title: str | None = None
    observed_at: str | None = None

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

        if self.observed_at is not None:
            if not isinstance(self.observed_at, str) or not self.observed_at.strip():
                raise ValueError(
                    "submitted evidence observed_at must be non-empty when provided"
                )
            normalized_observed_at = self.observed_at.strip()
            try:
                parsed_observed_at = datetime.fromisoformat(
                    normalized_observed_at.replace("Z", "+00:00")
                )
            except ValueError as exc:
                raise ValueError(
                    "submitted evidence observed_at must be a valid ISO-8601 timestamp"
                ) from exc
            if parsed_observed_at.tzinfo is None:
                raise ValueError(
                    "submitted evidence observed_at must include a timezone"
                )
            if parsed_observed_at.astimezone(timezone.utc) > datetime.now(timezone.utc):
                raise ValueError(
                    "submitted evidence observed_at cannot be in the future"
                )
            object.__setattr__(
                self,
                "observed_at",
                parsed_observed_at.astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            )

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
            observed_at=value.get("observed_at"),
        )

    def source_dict(self) -> dict[str, Any]:
        """Return the source and its exact text for auditable claim lineage.

        Keep observed_at in the separate source-observation contract, which
        records whether it was caller-supplied or merely ingestion time.
        """
        return {
            "title": self.title,
            "uri": self.uri,
            "content": self.content.strip(),
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
            # Consume at most one over-limit item. Caller-provided iterables
            # can be lazy or infinite; never materialize all their documents.
            normalized = tuple(
                SubmittedEvidenceDocument.from_mapping(document)
                for document in islice(documents, MAX_SUBMITTED_DOCUMENTS + 1)
            )
        except TypeError as exc:
            raise ValueError(
                "submitted evidence documents must be iterable"
            ) from exc
        return cls(normalized)

    def to_evidence(self) -> dict[str, Any]:
        """Build source-scoped evidence that can be independently re-extracted.

        The top-level body is only the deterministic aggregation of original
        per-source texts; it is not a separately attributed publication.
        """
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

    def validate_freshness_policy(
        self,
        max_age_seconds: float | int | None,
    ) -> None:
        if max_age_seconds is None:
            return
        if not is_positive_finite_number(max_age_seconds):
            raise ValueError(
                "freshness_max_age_seconds must be a positive number or None"
            )
        if any(document.observed_at is None for document in self.documents):
            raise ValueError(
                "freshness_max_age_seconds requires observed_at for every document"
            )

    def build_observations(
        self,
        provenance: SourceProvenanceResult,
        clock: Callable[[], datetime] | None = None,
    ) -> SourceObservationResult:
        if not isinstance(provenance, SourceProvenanceResult):
            raise ValueError(
                "provenance must be a SourceProvenanceResult"
            )
        if provenance.status == "unavailable":
            return SourceObservationResult.unavailable_result(
                provenance.reason or "source_provenance_unavailable"
            )
        if provenance.status == "empty":
            return SourceObservationResult.empty_result()

        now = (clock or (lambda: datetime.now(timezone.utc)))()
        if not isinstance(now, datetime) or now.tzinfo is None:
            raise ValueError("clock must return a timezone-aware datetime")
        ingestion_timestamp = (
            now.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
        document_by_uri = {
            document.uri: document
            for document in self.documents
        }

        observations = []
        for source in provenance.sources:
            document = document_by_uri.get(source.uri)
            if document is None:
                raise ValueError(
                    "source provenance contains an unknown submitted evidence uri"
                )
            if document.observed_at is not None:
                timestamp = document.observed_at
                method = "submitted_evidence_observation"
            else:
                timestamp = ingestion_timestamp
                method = "submitted_evidence_ingestion"
            observations.append(
                SourceObservation(
                    source_id=source.source_id,
                    observed_at=timestamp,
                    observation_method=method,
                )
            )

        return SourceObservationResult.usable_result(
            tuple(observations)
        )

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
                reason = result.reason or "claim_extraction_unavailable"
                # The extractor's Step 184 budget protects each completed
                # source document. Translate it to the submitted-evidence
                # surface instead of exposing a misleading retrieval reason.
                if reason == "retrieved_claim_limit_exceeded":
                    reason = "submitted_claim_limit_exceeded"
                return ClaimExtractionResult.unavailable_result(
                    reason,
                    source_count=len(self.documents),
                )

            for claim in result.claims:
                key = claim.text.casefold()
                existing = claims_by_key.get(key)
                if existing is None:
                    # The per-document limit alone is insufficient: 20 valid
                    # documents can each introduce new candidate claims.
                    # Reject globally without returning a partial claim graph.
                    if len(claims_by_key) >= MAX_SUBMITTED_CLAIMS:
                        return ClaimExtractionResult.unavailable_result(
                            "submitted_claim_limit_exceeded",
                            source_count=len(self.documents),
                        )
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
    "MAX_SUBMITTED_CLAIMS",
    "MAX_SUBMITTED_DOCUMENTS",
    "MAX_SUBMITTED_TITLE_CHARS",
    "MAX_SUBMITTED_URI_CHARS",
    "SubmittedEvidenceBundle",
    "SubmittedEvidenceDocument",
]
