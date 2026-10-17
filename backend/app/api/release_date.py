"""Step253 authenticated source-observation transport, no model trust claims.

The server reports only a date FIELD observed on one exactly scoped official
Python version page. It does not itself answer open-domain questions or
execute an LLM; the separately opted-in developer client generates a value
and independently verifies it against this source-bound observation.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.reality.freshness_policy import is_positive_finite_number
from backend.app.reality.independent_source_text_assurance import _safe_observer_source_uri
from backend.app.reality.reality_entity import normalize_explicit_entity_name


class ReleaseDateSourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=200, strict=True)
    entity: str = Field(min_length=1, max_length=100, strict=True)
    source_uri: str = Field(min_length=1, max_length=2048, strict=True)
    freshness_max_age_seconds: float | int = 3600

    @field_validator("entity")
    @classmethod
    def entity_valid(cls, v: str) -> str:
        return normalize_explicit_entity_name(v)

    @field_validator("source_uri")
    @classmethod
    def url_valid(cls, v: str) -> str:
        if not _safe_observer_source_uri(v):
            raise ValueError("invalid_original_source")
        return v

    @field_validator("freshness_max_age_seconds", mode="before")
    @classmethod
    def freshness_valid(cls, v: object) -> object:
        if not is_positive_finite_number(v):
            raise ValueError("invalid_source_freshness_window")
        return v


def release_date_binding(request: ReleaseDateSourceRequest) -> str:
    if not isinstance(request, ReleaseDateSourceRequest):
        raise TypeError("invalid_request")
    canonical = json.dumps(request.model_dump(mode="json"), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=True,
                           allow_nan=False).encode("utf-8")
    return sha256(canonical).hexdigest()


class ReleaseDateSourceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_uri: str = Field(min_length=1, max_length=2048)
    original_source_quote: str = Field(min_length=1, max_length=80)
    source_quote_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_capture_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_capture_observed_at: str = Field(min_length=1, max_length=64)


class ReleaseDateSourceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Literal["source_date_observed", "abstain"]
    reason_code: Literal[
        "unique_release_date_observed", "invalid_question_or_identity",
        "source_not_operator_allowed", "source_unavailable",
        "source_ambiguous_or_unverified", "source_capture_invalid",
    ]
    request_binding_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    citation: ReleaseDateSourceCitation | None = None
    original_source_observed: bool = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    model_used_for_source_verification: Literal[False] = False
    general_question_answering: Literal[False] = False


__all__ = [
    "ReleaseDateSourceRequest", "ReleaseDateSourceCitation",
    "ReleaseDateSourceResponse", "release_date_binding",
]
