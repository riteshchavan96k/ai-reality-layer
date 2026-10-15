"""Step250 strict API contract for explicit live-to-history source comparison.

There is never a history write, background source poll or proof of objective
truth. Historical baselines can be old but fresh evidence must be independently
observed in one exact allowlisted HTTPS source request.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from backend.app.api.temporal_timeline import TemporalTimelineRequest

_ID = r"^[0-9a-f]{32}$"
_SHA = r"^[0-9a-f]{64}$"
Decision = Literal["bounded_source_support", "bounded_source_contradiction"]
Status = Literal[
    "capture_unchanged", "capture_changed_statement_unchanged",
    "bounded_statement_changed",
]


class TemporalRecheckRequest(TemporalTimelineRequest):
    model_config = ConfigDict(extra="forbid", strict=True)


class TemporalRecheckEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_quote_sha256: str = Field(pattern=_SHA)
    source_capture_sha256: str = Field(pattern=_SHA)
    source_capture_observed_at: str = Field(min_length=20, max_length=64)
    decision: Decision


class TemporalRecheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    outcome: Literal["bounded_reconciliation", "abstain"]
    reason: Literal[
        "fresh_original_source_compared_to_historical",
        "reconciliation_not_enabled",
        "history_unavailable_or_invalid",
        "fresh_evidence_unavailable_or_ambiguous",
        "timeline_changed_during_recheck",
    ]
    request_binding_sha256: str = Field(pattern=_SHA)
    root_record_id: str = Field(pattern=_ID)
    baseline_record_id: str | None = Field(default=None, pattern=_ID)
    change_status: Status | None = None
    previous: TemporalRecheckEvidence | None = None
    current: TemporalRecheckEvidence | None = None
    may_use_current_as_bounded_evidence: bool = False
    may_use_historical_as_current_evidence: Literal[False] = False
    timeline_was_modified: Literal[False] = False
    historical_receipt_authenticated: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    factual_truth_verified: Literal[False] = False
    automatic_monitoring_enabled: Literal[False] = False
    externally_deployed: Literal[False] = False
