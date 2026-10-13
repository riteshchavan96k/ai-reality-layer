"""Strict source-selected claim request: no caller-supplied evidence excerpt.

A selected HTTPS URL is a *candidate*, not authority. The backend must
independently observe an exact operator-approved source and preserve its
conservative policy. This endpoint is not general web search or semantic AI.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.api.reality_state import RealityStateResponse
from backend.app.reality.freshness_policy import is_positive_finite_number
from backend.app.reality.independent_source_text_assurance import _safe_observer_source_uri
from backend.app.reality.reality_entity import (
    MAX_REALITY_ENTITY_NAME_CHARS,
    normalize_explicit_entity_name,
)


class OriginalSourceClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_text: str = Field(min_length=1, max_length=500)
    entity: str = Field(min_length=1, max_length=MAX_REALITY_ENTITY_NAME_CHARS)
    source_uri: str = Field(min_length=1, max_length=2048)
    freshness_max_age_seconds: float | int = 3600

    @field_validator("claim_text")
    @classmethod
    def checked_claim(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("claim_text may not be blank")
        return value

    @field_validator("entity")
    @classmethod
    def checked_entity(cls, value: str) -> str:
        return normalize_explicit_entity_name(value)

    @field_validator("source_uri")
    @classmethod
    def checked_source_uri(cls, value: str) -> str:
        if not _safe_observer_source_uri(value):
            raise ValueError("source_uri must be an HTTPS original-source candidate")
        return value

    @field_validator("freshness_max_age_seconds", mode="before")
    @classmethod
    def checked_window(cls, value: object) -> object:
        if not is_positive_finite_number(value):
            raise ValueError("freshness_max_age_seconds must be positive and finite")
        return value


class OriginalSourceEvidence(BaseModel):
    """Exact server-observed standalone unit, not publisher-signed truth."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_capture_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_capture_observed_at: str = Field(min_length=1, max_length=64)


class OriginalSourceClaimResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["supported", "uncertain", "insufficient", "unavailable"]
    reason: Literal[
        "claim_grammar_unsupported",
        "reader_not_configured",
        "source_not_operator_allowed",
        "source_unavailable",
        "no_unique_bounded_assertion",
        "bounded_reality_state_evaluated",
    ]
    source_ref: str | None = None
    request_binding_sha256: str
    reality_state: RealityStateResponse | None = None
    source_evidence: OriginalSourceEvidence | None = None


__all__ = [
    "OriginalSourceClaimRequest", "OriginalSourceClaimResponse", "OriginalSourceEvidence"
]
