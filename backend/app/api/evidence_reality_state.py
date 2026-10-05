from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.reality.freshness_policy import is_positive_finite_number

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
    observed_at: str | None = None

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
        from datetime import datetime, timezone

        normalized = value.strip()
        if not normalized:
            raise ValueError("observed_at must not be blank when provided")
        try:
            parsed = datetime.fromisoformat(
                normalized.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                "observed_at must be a valid ISO-8601 timestamp"
            ) from exc
        if parsed.tzinfo is None:
            raise ValueError("observed_at must include a timezone")
        if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
            raise ValueError("observed_at cannot be in the future")
        return (
            parsed.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )


class EvidenceRealityStateRequest(BaseModel):
    """Request contract for building a Reality State from supplied evidence."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1, max_length=10_000)
    documents: list[EvidenceDocumentInput] = Field(
        min_length=1,
        max_length=MAX_SUBMITTED_DOCUMENTS,
    )
    freshness_max_age_seconds: float | int | None = None

    @field_validator("task")
    @classmethod
    def validate_task(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("task must not be blank")
        return normalized

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
            if any(
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
