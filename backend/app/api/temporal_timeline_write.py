"""Step251 strict API contracts: privileged explicit source-history lifecycle."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from backend.app.api.original_source_claim import OriginalSourceClaimRequest

_ID = r"^[0-9a-f]{32}$"
_SHA = r"^[0-9a-f]{64}$"


class TimelineCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    operation_id: str = Field(pattern=_ID)
    claim: OriginalSourceClaimRequest


class TimelineAppendRequest(TimelineCreateRequest):
    root_record_id: str = Field(pattern=_ID)
    expected_latest_record_id: str = Field(pattern=_ID)


class TimelineWriteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    outcome: Literal["created", "appended", "abstain"]
    reason: Literal[
        "verified_observation_persisted", "write_not_available",
        "history_unavailable_or_invalid", "source_unavailable_or_ambiguous",
        "timeline_stale_or_conflicting",
    ]
    operation_id: str = Field(pattern=_ID)
    request_binding_sha256: str = Field(pattern=_SHA)
    root_record_id: str | None = Field(default=None, pattern=_ID)
    record_id: str | None = Field(default=None, pattern=_ID)
    sequence: int | None = Field(default=None, ge=0, le=63)
    change_status: Literal[
        "baseline", "capture_unchanged", "capture_changed_statement_unchanged",
        "bounded_statement_changed",
    ] | None = None
    decision: Literal["bounded_source_support", "bounded_source_contradiction"] | None = None
    source_quote_sha256: str | None = Field(default=None, pattern=_SHA)
    source_capture_sha256: str | None = Field(default=None, pattern=_SHA)
    source_capture_observed_at: str | None = Field(default=None, min_length=20, max_length=64)
    replayed: bool = False
    may_use_historical_as_current_evidence: Literal[False] = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    historical_receipt_authenticated: Literal[False] = False
    automatic_monitoring_enabled: Literal[False] = False
    externally_deployed: Literal[False] = False


__all__ = ["TimelineCreateRequest", "TimelineAppendRequest", "TimelineWriteResponse"]
