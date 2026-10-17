"""Step255 narrowly source-grounded direct-answer API, with no model dependency."""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.api.release_date import ReleaseDateSourceCitation
from backend.app.reality.freshness_policy import is_positive_finite_number
from backend.app.reality.reality_entity import normalize_explicit_entity_name


class EvidenceFirstAskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=200, strict=True)
    entity: str = Field(min_length=1, max_length=100, strict=True)
    freshness_max_age_seconds: float | int = 3600

    @field_validator("entity")
    @classmethod
    def validated_entity(cls, value: str) -> str:
        return normalize_explicit_entity_name(value)

    @field_validator("freshness_max_age_seconds", mode="before")
    @classmethod
    def validated_freshness(cls, value: object) -> object:
        if not is_positive_finite_number(value):
            raise ValueError("invalid_freshness_max_age_seconds")
        return value


def ask_request_binding(request: EvidenceFirstAskRequest) -> str:
    if not isinstance(request, EvidenceFirstAskRequest):
        raise TypeError("validated_request_required")
    raw = json.dumps(
        request.model_dump(mode="json"),
        sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(b"arl-step255-evidence-first-ask-v1:"+raw).hexdigest()


class EvidenceFirstAskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Literal["bounded_source_answer", "abstain"]
    reason_code: Literal[
        "independent_original_source_answer",
        "unsupported_question",
        "source_not_operator_allowed",
        "source_unavailable_or_ambiguous",
    ]
    request_binding_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_request_binding_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    entity: str | None = None
    fact_kind: Literal["release_date", "release_type"] | None = None
    answer_value: str | None = Field(default=None, max_length=32)
    citation: ReleaseDateSourceCitation | None = None
    observed_source_support: bool = False
    model_executed: Literal[False] = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    general_question_answering: Literal[False] = False
    externally_deployed: Literal[False] = False


__all__ = [
    "EvidenceFirstAskRequest", "EvidenceFirstAskResponse", "ask_request_binding",
]
