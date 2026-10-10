from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

from backend.app.reality.freshness_policy import is_positive_finite_number
from backend.app.reality.reality_entity import (
    MAX_REALITY_ENTITY_NAME_CHARS,
    normalize_explicit_entity_name,
)

from backend.app.reality.source_observation import (
    MAX_SOURCE_OBSERVED_AT_CHARS,
    normalize_reported_observation_time,
)
from backend.app.reality.submitted_evidence import (
    MAX_SUBMITTED_CONTENT_CHARS,
    MAX_SUBMITTED_DOCUMENTS,
    MAX_SUBMITTED_TITLE_CHARS,
    MAX_SUBMITTED_URI_CHARS,
)


class EvidenceDocumentInput(BaseModel):
    """One source-scoped evidence document supplied by an API client."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=MAX_SUBMITTED_CONTENT_CHARS)
    uri: str = Field(min_length=1, max_length=MAX_SUBMITTED_URI_CHARS)
    title: str | None = Field(default=None, max_length=MAX_SUBMITTED_TITLE_CHARS)
    observed_at: str | None = Field(
        default=None, max_length=MAX_SOURCE_OBSERVED_AT_CHARS
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("content must not be blank")
        return normalized

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, value: str) -> str:
        normalized = value.strip()
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("uri must use http or https")
        return normalized

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("title must not be blank when provided")
        return normalized


    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_reported_observation_time(value)


class EvidenceRealityStateRequest(BaseModel):
    """Request contract for building a Reality State from supplied evidence."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1, max_length=10_000)
    entity: str | None = Field(
        default=None,
        max_length=MAX_REALITY_ENTITY_NAME_CHARS,
    )
    documents: list[EvidenceDocumentInput] = Field(
        min_length=1,
        max_length=MAX_SUBMITTED_DOCUMENTS,
    )
    freshness_max_age_seconds: float | int | None = None
    require_independent_source_text_match: StrictBool = False

    @field_validator("task")
    @classmethod
    def validate_task(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("task must not be blank")
        return normalized

    @field_validator("entity", mode="before")
    @classmethod
    def validate_entity(cls, value: object) -> object:
        if value is None:
            return None
        return normalize_explicit_entity_name(value)

    @field_validator("freshness_max_age_seconds", mode="before")
    @classmethod
    def validate_freshness_window(
        cls,
        value: object,
    ) -> object:
        if value is None:
            return None
        if not is_positive_finite_number(value):
            raise ValueError(
                "freshness_max_age_seconds must be a positive number"
            )
        return value

    @model_validator(mode="after")
    def validate_request_consistency(self) -> "EvidenceRealityStateRequest":
        uris = [document.uri for document in self.documents]
        if len(set(uris)) != len(uris):
            raise ValueError("document uris must be unique")

        if self.freshness_max_age_seconds is not None:
            value = self.freshness_max_age_seconds
            if not is_positive_finite_number(value):
                raise ValueError(
                    "freshness_max_age_seconds must be a positive number"
                )
            # Strict mode may use server-observed capture times instead of
            # client-supplied timestamps. The service must fail closed if
            # neither a trusted capture nor a reported time is available.
            if not self.require_independent_source_text_match and any(
                document.observed_at is None
                for document in self.documents
            ):
                raise ValueError(
                    "freshness_max_age_seconds requires observed_at "
                    "for every document"
                )
        return self


__all__ = [
    "EvidenceDocumentInput",
    "EvidenceRealityStateRequest",
]
