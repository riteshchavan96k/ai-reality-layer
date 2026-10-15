"""Step249 defensive AI-app consumer of operator-controlled historical evidence.

Not a publisher authenticator. Requires a trusted authenticated TLS transport
(or controlled same-process TestClient). Cryptographic source origin, historical
authority, real-world truth and current evidence are ALWAYS unverified.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
import re

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.api.temporal_timeline import TemporalTimelineResponse, TemporalTimelineRequest
from backend.app.integrations.ai_claim_gate import MAX_API_RESPONSE_BYTES

TIMELINE_PATH = "/api/v1/reality-state/timeline"
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED_CHANGES = {
    "capture_unchanged", "capture_changed_statement_unchanged",
    "bounded_statement_changed",
}


@dataclass(frozen=True)
class HistoricalObservation:
    sequence: int
    record_id: str
    change_from_previous: str
    decision: str
    source_quote_sha256: str
    source_capture_sha256: str
    source_capture_observed_at: str


@dataclass(frozen=True)
class ClientTemporalTimeline:
    outcome: Literal["verified_historical_timeline", "abstain"]
    request_binding_sha256: str
    root_record_id: str
    reason_code: str
    latest_record_id: str | None = None
    observations: tuple[HistoricalObservation, ...] = ()
    may_use_as_current_evidence: Literal[False] = False
    historical_receipt_authenticated: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    factual_truth_verified: Literal[False] = False
    automatic_monitoring_enabled: Literal[False] = False
    externally_deployed: Literal[False] = False


def _abstain(request: OriginalSourceClaimRequest, root: str) -> ClientTemporalTimeline:
    return ClientTemporalTimeline(
        outcome="abstain", reason_code="api_unavailable_or_invalid",
        request_binding_sha256=claim_request_binding_sha256(request),
        root_record_id=root,
    )


def interpret_temporal_timeline(
    raw: object, request: OriginalSourceClaimRequest, root: str,
    *, now: datetime | None = None,
) -> ClientTemporalTimeline:
    """Defend against altered or overclaiming API responses, fail closed."""
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("validated request required")
    if type(root) is not str or _HEX32.fullmatch(root) is None:
        return _abstain(request, root)
    if not isinstance(raw, dict):
        return _abstain(request, root)
    try:
        # Do not let Pydantic coerce false-like values such as 0 to False.
        flags = (
            "may_use_as_current_evidence", "historical_receipt_authenticated",
            "publisher_authorship_verified", "factual_truth_verified",
            "automatic_monitoring_enabled", "externally_deployed",
        )
        if any(type(raw.get(k)) is not bool or raw[k] is not False for k in flags):
            return _abstain(request, root)
        parsed = TemporalTimelineResponse.model_validate(raw)
        binding = claim_request_binding_sha256(request)
        if (
            parsed.root_record_id != root or parsed.request_binding_sha256 != binding
        ):
            return _abstain(request, root)
        if parsed.outcome == "abstain":
            if (
                parsed.reason == "operator_history_validated"
                or parsed.timeline is not None
            ):
                return _abstain(request, root)
            return _abstain(request, root)
        if (
            parsed.outcome != "verified_historical_timeline"
            or parsed.reason != "operator_history_validated"
            or parsed.timeline is None
        ):
            return _abstain(request, root)
        t = parsed.timeline
        if any(type(raw["timeline"].get(k)) is not bool
               or raw["timeline"][k] is not False
               for k in flags if k != "may_use_as_current_evidence"):
            return _abstain(request, root)
        if (
            t.root_record_id != root or t.request_binding_sha256 != binding
            or t.total_observations != len(t.observations)
            or t.linked_history is not (len(t.observations) > 1)
            or t.latest_record_id != t.observations[-1].record_id
            or t.observations[0].record_id != root
        ):
            return _abstain(request, root)
        clock = datetime.now(timezone.utc) if now is None else now
        if clock.tzinfo is None or clock.utcoffset() is None:
            return _abstain(request, root)
        previous = None
        ids = set()
        checked = []
        for i, item in enumerate(t.observations):
            if item.sequence != i or item.record_id in ids:
                return _abstain(request, root)
            ids.add(item.record_id)
            if not item.source_capture_observed_at.endswith("Z"):
                return _abstain(request, root)
            moment = datetime.fromisoformat(
                item.source_capture_observed_at.replace("Z", "+00:00")
            )
            if (
                moment.tzinfo is None or moment.utcoffset() is None
                or moment > clock + timedelta(seconds=30)
            ):
                return _abstain(request, root)
            if i == 0:
                if item.change_from_previous != "baseline":
                    return _abstain(request, root)
            else:
                if moment < previous[0]:
                    return _abstain(request, root)
                same_capture = item.source_capture_sha256 == previous[1].source_capture_sha256
                same_statement = (
                    item.source_quote_sha256 == previous[1].source_quote_sha256
                    and item.decision == previous[1].decision
                )
                actual = (
                    "capture_unchanged" if same_capture
                    else "capture_changed_statement_unchanged" if same_statement
                    else "bounded_statement_changed"
                )
                if (
                    item.change_from_previous not in _ALLOWED_CHANGES
                    or (same_capture and not same_statement)
                    or item.change_from_previous != actual
                ):
                    return _abstain(request, root)
            checked.append(HistoricalObservation(
                sequence=i, record_id=item.record_id,
                change_from_previous=item.change_from_previous,
                decision=item.decision,
                source_quote_sha256=item.source_quote_sha256,
                source_capture_sha256=item.source_capture_sha256,
                source_capture_observed_at=item.source_capture_observed_at,
            ))
            previous = (moment, item)
        return ClientTemporalTimeline(
            outcome="verified_historical_timeline",
            reason_code="operator_history_validated",
            request_binding_sha256=binding,
            root_record_id=root, latest_record_id=t.latest_record_id,
            observations=tuple(checked),
        )
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError):
        return _abstain(request, root)


def check_temporal_timeline_with_api(
    client: Any, token: str, request: OriginalSourceClaimRequest, root: str,
) -> ClientTemporalTimeline:
    """One authenticated history POST; does not authorize any source fetch."""
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("validated claim required")
    if type(root) is not str or _HEX32.fullmatch(root) is None:
        return _abstain(request, root)
    if (
        type(token) is not str or not token.isascii()
        or not 32 <= len(token) <= 256
        or any(ord(ch) < 33 or ord(ch) > 126 for ch in token)
    ):
        return _abstain(request, root)
    try:
        body = TemporalTimelineRequest(
            root_record_id=root, claim=request,
        )
        response = client.post(
            TIMELINE_PATH, json=body.model_dump(mode="json"),
            headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        )
        payload = response.content
        if (
            response.status_code != 200
            or not isinstance(payload, bytes)
            or len(payload) > MAX_API_RESPONSE_BYTES
            or "application/json" not in response.headers.get("content-type", "").lower()
        ):
            return _abstain(request, root)
        return interpret_temporal_timeline(response.json(), request, root)
    except Exception:
        return _abstain(request, root)


__all__ = [
    "TIMELINE_PATH", "HistoricalObservation", "ClientTemporalTimeline",
    "interpret_temporal_timeline", "check_temporal_timeline_with_api",
]
