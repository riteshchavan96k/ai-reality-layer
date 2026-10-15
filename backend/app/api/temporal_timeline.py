"""Strict historical-source timeline API contract. Never claims current truth.

The root identifies operator-held local history, not a globally trusted or
publisher-signed record. Read access requires pilot authentication and exact
source authorization. Returned metadata excludes untrusted original-source quotes.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.app.api.original_source_claim import OriginalSourceClaimRequest

_ID_PATTERN = r"^[0-9a-f]{32}$"
_SHA_PATTERN = r"^[0-9a-f]{64}$"
Decision = Literal["bounded_source_support", "bounded_source_contradiction"]
Change = Literal["baseline", "capture_unchanged",
                 "capture_changed_statement_unchanged", "bounded_statement_changed"]


class TemporalTimelineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    root_record_id: str = Field(pattern=_ID_PATTERN)
    claim: OriginalSourceClaimRequest


class TemporalTimelineObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sequence: int = Field(ge=0, le=63)
    record_id: str = Field(pattern=_ID_PATTERN)
    change_from_previous: Change
    decision: Decision
    source_quote_sha256: str = Field(pattern=_SHA_PATTERN)
    source_capture_sha256: str = Field(pattern=_SHA_PATTERN)
    source_capture_observed_at: str = Field(min_length=20, max_length=64)


class TemporalTimelineSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scope: Literal["operator_held_original_source_timeline"]
    root_record_id: str = Field(pattern=_ID_PATTERN)
    request_binding_sha256: str = Field(pattern=_SHA_PATTERN)
    total_observations: int = Field(ge=1, le=64)
    linked_history: bool
    latest_record_id: str = Field(pattern=_ID_PATTERN)
    observations: list[TemporalTimelineObservation] = Field(min_length=1, max_length=64)
    historical_receipt_authenticated: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    factual_truth_verified: Literal[False] = False
    automatic_monitoring_enabled: Literal[False] = False
    externally_deployed: Literal[False] = False


class TemporalTimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    outcome: Literal["verified_historical_timeline", "abstain"]
    reason: Literal["operator_history_validated", "history_unavailable_or_invalid",
                    "timeline_api_not_enabled"]
    request_binding_sha256: str = Field(pattern=_SHA_PATTERN)
    root_record_id: str = Field(pattern=_ID_PATTERN)
    timeline: TemporalTimelineSummary | None = None
    may_use_as_current_evidence: Literal[False] = False
    historical_receipt_authenticated: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    factual_truth_verified: Literal[False] = False
    automatic_monitoring_enabled: Literal[False] = False
    externally_deployed: Literal[False] = False


__all__ = [
    "TemporalTimelineRequest", "TemporalTimelineResponse",
    "TemporalTimelineSummary", "TemporalTimelineObservation",
]
