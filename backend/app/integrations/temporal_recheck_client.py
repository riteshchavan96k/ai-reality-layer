"""Defensive Step250 client for one explicitly authorized live/history comparison.

Trusted TLS/authenticated transport required. Never interprets hash consistency
as publisher authentication, objective truth, or historical attestation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Literal

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.api.temporal_recheck import TemporalRecheckRequest, TemporalRecheckResponse
from backend.app.integrations.ai_claim_gate import MAX_API_RESPONSE_BYTES

RECHECK_PATH = "/api/v1/reality-state/timeline/recheck"
_ID = re.compile(r"[0-9a-f]{32}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ClientTemporalReconciliation:
    outcome: Literal["bounded_reconciliation", "abstain"]
    root_record_id: str
    request_binding_sha256: str
    reason_code: str
    baseline_record_id: str | None = None
    change_status: str | None = None
    previous_capture_sha256: str | None = None
    current_capture_sha256: str | None = None
    previous_quote_sha256: str | None = None
    current_quote_sha256: str | None = None
    previous_decision: str | None = None
    current_decision: str | None = None
    current_capture_observed_at: str | None = None
    may_use_current_as_bounded_evidence: bool = False
    may_use_historical_as_current_evidence: Literal[False] = False
    factual_truth_verified: Literal[False] = False
    historical_receipt_authenticated: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    automatic_monitoring_enabled: Literal[False] = False
    timeline_was_modified: Literal[False] = False
    externally_deployed: Literal[False] = False


def _abstain(req: OriginalSourceClaimRequest, root: str) -> ClientTemporalReconciliation:
    return ClientTemporalReconciliation(
        outcome="abstain", reason_code="api_unavailable_or_invalid",
        root_record_id=root, request_binding_sha256=claim_request_binding_sha256(req),
    )


def interpret_temporal_reconciliation(
    data: object, req: OriginalSourceClaimRequest, root: str, *,
    now: datetime | None = None,
) -> ClientTemporalReconciliation:
    if not isinstance(req, OriginalSourceClaimRequest):
        raise TypeError("validated claim is required")
    if type(root) is not str or _ID.fullmatch(root) is None or type(data) is not dict:
        return _abstain(req, root)
    try:
        flags = (
            "may_use_historical_as_current_evidence", "timeline_was_modified",
            "factual_truth_verified", "historical_receipt_authenticated",
            "publisher_authorship_verified", "automatic_monitoring_enabled",
            "externally_deployed",
        )
        if any(type(data.get(k)) is not bool or data[k] is not False for k in flags):
            return _abstain(req, root)
        if type(data.get("may_use_current_as_bounded_evidence")) is not bool:
            return _abstain(req, root)
        parsed = TemporalRecheckResponse.model_validate(data)
        if parsed.root_record_id != root or parsed.request_binding_sha256 != claim_request_binding_sha256(req):
            return _abstain(req, root)
        if parsed.outcome == "abstain":
            if (parsed.baseline_record_id is not None or parsed.previous is not None
                or parsed.current is not None or parsed.change_status is not None
                or parsed.may_use_current_as_bounded_evidence is not False
                or parsed.reason == "fresh_original_source_compared_to_historical"):
                return _abstain(req, root)
            return _abstain(req, root)
        if (parsed.outcome != "bounded_reconciliation"
            or parsed.reason != "fresh_original_source_compared_to_historical"
            or parsed.baseline_record_id is None or parsed.previous is None
            or parsed.current is None or parsed.change_status is None):
            return _abstain(req, root)
        prev, fresh = parsed.previous, parsed.current
        now_time = datetime.now(timezone.utc) if now is None else now
        if now_time.tzinfo is None or now_time.utcoffset() is None:
            return _abstain(req, root)
        if (not prev.source_capture_observed_at.endswith("Z")
            or not fresh.source_capture_observed_at.endswith("Z")):
            return _abstain(req, root)
        old_time = datetime.fromisoformat(prev.source_capture_observed_at.replace("Z", "+00:00"))
        current_time = datetime.fromisoformat(fresh.source_capture_observed_at.replace("Z", "+00:00"))
        if (old_time.tzinfo is None or current_time.tzinfo is None
            or current_time < old_time
            or current_time > now_time + timedelta(seconds=30)
            or old_time > now_time + timedelta(seconds=30)
            or current_time < now_time - timedelta(seconds=req.freshness_max_age_seconds)):
            return _abstain(req, root)
        same_capture = prev.source_capture_sha256 == fresh.source_capture_sha256
        same_statement = (
            prev.source_quote_sha256 == fresh.source_quote_sha256
            and prev.decision == fresh.decision
        )
        if same_capture and not same_statement:
            return _abstain(req, root)
        expected = (
            "capture_unchanged" if same_capture
            else "capture_changed_statement_unchanged" if same_statement
            else "bounded_statement_changed"
        )
        if (expected != parsed.change_status
            or parsed.may_use_current_as_bounded_evidence is not (
                fresh.decision == "bounded_source_support"
            )):
            return _abstain(req, root)
        return ClientTemporalReconciliation(
            outcome="bounded_reconciliation", reason_code=parsed.reason,
            request_binding_sha256=parsed.request_binding_sha256,
            root_record_id=root, baseline_record_id=parsed.baseline_record_id,
            change_status=parsed.change_status,
            previous_capture_sha256=prev.source_capture_sha256,
            current_capture_sha256=fresh.source_capture_sha256,
            previous_quote_sha256=prev.source_quote_sha256,
            current_quote_sha256=fresh.source_quote_sha256,
            previous_decision=prev.decision, current_decision=fresh.decision,
            current_capture_observed_at=fresh.source_capture_observed_at,
            may_use_current_as_bounded_evidence=parsed.may_use_current_as_bounded_evidence,
        )
    except (ValueError, TypeError, AttributeError, IndexError, OverflowError):
        return _abstain(req, root)


def check_temporal_reconciliation_with_api(
    client: Any, token: str, req: OriginalSourceClaimRequest, root: str,
) -> ClientTemporalReconciliation:
    """At most one authenticated reconciliation POST; no hidden retry."""
    if not isinstance(req, OriginalSourceClaimRequest):
        raise TypeError("validated claim required")
    if type(root) is not str or _ID.fullmatch(root) is None:
        return _abstain(req, root)
    if (type(token) is not str or not token.isascii()
        or not 32 <= len(token) <= 256
        or any(ord(ch) < 33 or ord(ch) > 126 for ch in token)):
        return _abstain(req, root)
    try:
        body = TemporalRecheckRequest(root_record_id=root, claim=req)
        response = client.post(
            RECHECK_PATH, json=body.model_dump(mode="json"),
            headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        )
        raw = response.content
        if (response.status_code != 200 or type(raw) is not bytes
            or len(raw) > MAX_API_RESPONSE_BYTES
            or "application/json" not in response.headers.get("content-type", "").lower()):
            return _abstain(req, root)
        return interpret_temporal_reconciliation(response.json(), req, root)
    except Exception:
        return _abstain(req, root)


__all__ = [
    "RECHECK_PATH", "ClientTemporalReconciliation",
    "interpret_temporal_reconciliation", "check_temporal_reconciliation_with_api",
]
