from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class EvidenceRealityStateRequest(BaseModel):
    """Request contract for building a Reality State from supplied evidence."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1, max_length=10_000)
    documents: list[EvidenceDocumentInput] = Field(
        min_length=1,
        max_length=MAX_SUBMITTED_DOCUMENTS,
    )

    @field_validator("task")
    @classmethod
    def validate_task(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("task must not be blank")
        return normalized

    @model_validator(mode="after")
    def validate_unique_source_uris(self) -> "EvidenceRealityStateRequest":
        uris = [document.uri for document in self.documents]
        if len(set(uris)) != len(uris):
            raise ValueError("document uris must be unique")
        return self


__all__ = [
    "EvidenceDocumentInput",
    "EvidenceRealityStateRequest",
]
