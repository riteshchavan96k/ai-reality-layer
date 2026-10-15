"""Step251 fail-closed privileged app client for explicit timeline mutations.

The caller must own a trusted TLS transport to the authenticated operator.
The independent write token and pilot bearer NEVER appear in returned reports.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from typing import Any

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.api.temporal_timeline_write import (
    TimelineCreateRequest, TimelineAppendRequest, TimelineWriteResponse,
)
from backend.app.integrations.ai_claim_gate import MAX_API_RESPONSE_BYTES

CREATE_PATH = "/api/v1/reality-state/timeline/create"
APPEND_PATH = "/api/v1/reality-state/timeline/append"
_ID = re.compile(r"[0-9a-f]{32}\Z")


@dataclass(frozen=True)
class ClientTimelineWrite:
    outcome: str
    operation_id: str
    request_binding_sha256: str
    reason_code: str
    root_record_id: str | None = None
    record_id: str | None = None
    sequence: int | None = None
    change_status: str | None = None
    decision: str | None = None
    replayed: bool = False
    may_use_historical_as_current_evidence: bool = False
    factual_truth_verified: bool = False
    publisher_authorship_verified: bool = False
    historical_receipt_authenticated: bool = False
    automatic_monitoring_enabled: bool = False
    externally_deployed: bool = False


def _abstain(claim: OriginalSourceClaimRequest, op: str) -> ClientTimelineWrite:
    return ClientTimelineWrite(
        outcome="abstain", operation_id=op,
        request_binding_sha256=claim_request_binding_sha256(claim),
        reason_code="api_unavailable_or_invalid",
    )


def _valid_secret(v: str) -> bool:
    return (
        type(v) is str and v.isascii()
        and 32 <= len(v) <= 256
        and all(33 <= ord(ch) <= 126 for ch in v)
    )


def interpret_timeline_write(
    raw: object, claim: OriginalSourceClaimRequest, op: str,
    *, root: str | None = None, expected: str | None = None,
    now: datetime | None = None,
) -> ClientTimelineWrite:
    if not isinstance(claim, OriginalSourceClaimRequest):
        raise TypeError("validated source claim required")
    if (type(op) is not str or _ID.fullmatch(op) is None
        or type(raw) is not dict):
        return _abstain(claim, op)
    try:
        for k in (
            "may_use_historical_as_current_evidence", "factual_truth_verified",
            "publisher_authorship_verified", "historical_receipt_authenticated",
            "automatic_monitoring_enabled", "externally_deployed",
        ):
            if type(raw.get(k)) is not bool or raw[k] is not False:
                return _abstain(claim, op)
        if type(raw.get("replayed")) is not bool:
            return _abstain(claim, op)
        parsed = TimelineWriteResponse.model_validate(raw)
        if (
            parsed.operation_id != op
            or parsed.request_binding_sha256 != claim_request_binding_sha256(claim)
        ):
            return _abstain(claim, op)
        if parsed.outcome == "abstain":
            if (parsed.root_record_id is not None or parsed.record_id is not None
                or parsed.sequence is not None or parsed.change_status is not None
                or parsed.decision is not None or parsed.source_capture_sha256 is not None
                or parsed.source_quote_sha256 is not None or parsed.source_capture_observed_at is not None
                or parsed.replayed or parsed.reason == "verified_observation_persisted"):
                return _abstain(claim, op)
            return _abstain(claim, op)
        if (
            parsed.reason != "verified_observation_persisted"
            or parsed.record_id is None or parsed.root_record_id is None
            or parsed.sequence is None or parsed.change_status is None
            or parsed.decision is None or parsed.source_capture_observed_at is None
            or parsed.source_quote_sha256 is None or parsed.source_capture_sha256 is None
        ):
            return _abstain(claim, op)
        if root is None and expected is None:
            if (parsed.outcome != "created"
                or parsed.sequence != 0 or parsed.change_status != "baseline"
                or parsed.record_id != parsed.root_record_id):
                return _abstain(claim, op)
        else:
            if (
                type(root) is not str or _ID.fullmatch(root) is None
                or type(expected) is not str or _ID.fullmatch(expected) is None
                or parsed.outcome != "appended" or parsed.root_record_id != root
                or parsed.record_id in (root, expected)
                or parsed.sequence < 1 or parsed.change_status == "baseline"
            ):
                return _abstain(claim, op)
        if not parsed.source_capture_observed_at.endswith("Z"):
            return _abstain(claim, op)
        observed = datetime.fromisoformat(
            parsed.source_capture_observed_at.replace("Z", "+00:00")
        )
        clock = datetime.now(timezone.utc) if now is None else now
        if (
            observed.tzinfo is None or clock.tzinfo is None
            or observed > clock + timedelta(seconds=30)
        ):
            return _abstain(claim, op)
        return ClientTimelineWrite(
            outcome=parsed.outcome, reason_code=parsed.reason,
            request_binding_sha256=parsed.request_binding_sha256,
            operation_id=op, root_record_id=parsed.root_record_id,
            record_id=parsed.record_id, sequence=parsed.sequence,
            change_status=parsed.change_status, decision=parsed.decision,
            replayed=parsed.replayed,
        )
    except (TypeError, ValueError, AttributeError, OverflowError):
        return _abstain(claim, op)


def write_timeline_with_api(
    client: Any, bearer: str, writer: str, claim: OriginalSourceClaimRequest,
    operation_id: str, *, root: str | None = None, expected: str | None = None,
) -> ClientTimelineWrite:
    """One authenticated create or append POST, with caller-owned retry ID."""
    if not isinstance(claim, OriginalSourceClaimRequest):
        raise TypeError("validated original-source claim required")
    if (type(operation_id) is not str or _ID.fullmatch(operation_id) is None
        or not _valid_secret(bearer) or not _valid_secret(writer)):
        return _abstain(claim, operation_id)
    try:
        if root is None and expected is None:
            path = CREATE_PATH
            body = TimelineCreateRequest(operation_id=operation_id, claim=claim)
        else:
            path = APPEND_PATH
            body = TimelineAppendRequest(
                operation_id=operation_id, claim=claim,
                root_record_id=root, expected_latest_record_id=expected,
            )
        response = client.post(
            path,
            json=body.model_dump(mode="json"),
            headers={
                "Authorization": "Bearer " + bearer,
                "X-ARL-Timeline-Write-Token": writer,
                "Accept": "application/json",
            },
        )
        data = response.content
        if (
            response.status_code != 200 or type(data) is not bytes
            or len(data) > MAX_API_RESPONSE_BYTES
            or "application/json" not in response.headers.get("content-type", "").lower()
        ):
            return _abstain(claim, operation_id)
        return interpret_timeline_write(
            response.json(), claim, operation_id, root=root, expected=expected,
        )
    except Exception:
        return _abstain(claim, operation_id)


__all__ = [
    "CREATE_PATH", "APPEND_PATH", "ClientTimelineWrite",
    "interpret_timeline_write", "write_timeline_with_api",
]
