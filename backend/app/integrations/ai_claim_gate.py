"""Fail-closed AI application's consumer for original-source claim Reality States.

Use with an explicitly configured, authenticated API transport (e.g. a local
FastAPI TestClient now, or TLS-verified client when deployment is authorized).
Does not choose an origin, fetch a publisher, execute AI actions, or load
credentials. It NEVER upgrades bounded text alignment into factual truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Literal

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import OriginalSourceClaimRequest

MAX_API_RESPONSE_BYTES = 512_000
CLAIM_PATH = "/api/v1/reality-state/claim"
_SHA = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class AIClaimGateDecision:
    decision: Literal["bounded_supported", "bounded_contradicted", "abstain"]
    may_use_as_bounded_evidence: bool
    reason_code: Literal[
        "bounded_source_alignment", "bounded_source_contradiction",
        "api_unavailable_or_invalid", "unverified_or_incomplete",
    ]
    source_ref: str | None = None
    capture_sha256: str | None = None
    capture_observed_at: str | None = None
    # Permanent explicit epistemic ceilings, not optional model conclusions.
    semantic_truth_verified: bool = False
    publisher_authorship_verified: bool = False


def _abstain(reason: str = "unverified_or_incomplete") -> AIClaimGateDecision:
    return AIClaimGateDecision("abstain", False, reason)


def _object(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def interpret_claim_reality_state(
    response: object,
    request: OriginalSourceClaimRequest,
    *,
    now: datetime | None = None,
) -> AIClaimGateDecision:
    """Interpret only trusted API responses; malformed/mixed state abstains."""
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be a validated OriginalSourceClaimRequest")
    data = _object(response)
    if (
        data.get("request_binding_sha256") != claim_request_binding_sha256(request)
        or data.get("source_ref") != request.source_uri
        or data.get("reason") != "bounded_reality_state_evaluated"
    ):
        return _abstain()

    state = _object(data.get("reality_state"))
    status = state.get("status")
    if (
        status not in {"supported", "uncertain", "insufficient", "unavailable"}
        or data.get("status") != status
        or state.get("assembly_method") != "deterministic_signal_snapshot"
    ):
        return _abstain()

    entity = _object(state.get("entity"))
    verification = _object(state.get("verification"))
    evidence = _object(state.get("evidence"))
    assurance = _object(evidence.get("independent_source_text_assurance"))
    alignment = _object(evidence.get("claim_alignment"))
    source_rows = assurance.get("sources")
    reasons = alignment.get("decision_reasons")
    decisions = alignment.get("source_decisions")
    if (
        entity.get("status") != "specified"
        or entity.get("name") != request.entity
        or entity.get("identification_method") != "explicit_input"
        or verification.get("status") != "completed"
        or verification.get("verification_method") != "deterministic_pipeline_snapshot"
        or assurance.get("status") != "exact_text_observed"
        or assurance.get("source_count") != 1
        or assurance.get("matched_source_count") != 1
        or assurance.get("publisher_authenticated") is not False
        or assurance.get("semantic_support_verified") is not False
        or alignment.get("method") != "bounded_atomic_assertion_comparison"
        or alignment.get("source_count") != 1
        or alignment.get("semantic_support_verified") is not False
        or alignment.get("factual_truth_verified") is not False
        or not isinstance(source_rows, list) or len(source_rows) != 1
        or not isinstance(reasons, list) or len(reasons) != 1
        or not isinstance(decisions, list) or len(decisions) != 1
    ):
        return _abstain()

    row = _object(source_rows[0])
    if (
        row.get("source_ref") != request.source_uri
        or row.get("status") != "exact_text_observed"
        or row.get("assertion_context_status") != "unique_standalone_unit"
        or row.get("source_counterstatement_status")
        != "no_bounded_counterstatement_observed"
        or row.get("source_quote_context_status")
        != "no_matching_html_quote_unit"
        or row.get("reason") is not None
        or not isinstance(row.get("capture_sha256"), str)
        or _SHA.fullmatch(row["capture_sha256"]) is None
        or not isinstance(row.get("capture_observed_at"), str)
        or _object(reasons[0]).get("source_ref") != request.source_uri
        or _object(decisions[0]).get("source_ref") != request.source_uri
    ):
        return _abstain()

    # Reject an old, implausibly future, or malformed observation even if an
    # intermediate component accidentally labels that source "fresh".
    try:
        captured = datetime.fromisoformat(
            row["capture_observed_at"].replace("Z", "+00:00")
        )
        current = datetime.now(timezone.utc) if now is None else now
        if (captured.tzinfo is None or current.tzinfo is None
            or not row["capture_observed_at"].endswith("Z")
            or captured > current + timedelta(seconds=30)
            or captured < current - timedelta(seconds=request.freshness_max_age_seconds)):
            return _abstain()
    except (TypeError, ValueError, OverflowError):
        return _abstain()

    freshness = _object(state.get("freshness"))
    conflicts = _object(state.get("conflicts"))
    confidence = _object(state.get("confidence_signals"))
    if (
        freshness.get("status") != "usable"
        or freshness.get("stale_count") != 0
        or freshness.get("unknown_count") != 0
        or conflicts.get("conflict_count") != 0
        or confidence.get("status") != status
    ):
        return _abstain()

    aligned = alignment.get("status") == "aligned"
    contradicted = alignment.get("status") == "contradicted"
    relation = "aligned" if aligned else "contradicted" if contradicted else None
    reason = (
        "bounded_assertion_aligned" if aligned
        else "bounded_assertion_contradicted" if contradicted else None
    )
    if (
        relation is None
        or _object(decisions[0]).get("relationship") != relation
        or _object(reasons[0]).get("code") != reason
        or (aligned and status != "supported")
        or (contradicted and status == "supported")
    ):
        return _abstain()

    if contradicted:
        return AIClaimGateDecision(
            "bounded_contradicted", False, "bounded_source_contradiction",
            request.source_uri, row["capture_sha256"], row["capture_observed_at"],
        )
    return AIClaimGateDecision(
        "bounded_supported", True, "bounded_source_alignment",
        request.source_uri, row["capture_sha256"], row["capture_observed_at"],
    )


def check_claim_with_api(
    client: Any,
    token: str,
    request: OriginalSourceClaimRequest,
) -> AIClaimGateDecision:
    """Perform one deliberate authenticated call using an injected API client.

    The caller owns transport authenticity/TLS and bearer secret storage.
    Any HTTP error, malformed JSON, oversized output or transport exception
    abstains; no response body, arbitrary exception or credential is logged.
    """
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be validated before a network call")
    if (
        not isinstance(token, str)
        or not token.isascii()
        or not 32 <= len(token) <= 256
        or any(ord(c) < 33 or ord(c) > 126 for c in token)
    ):
        return _abstain("api_unavailable_or_invalid")
    try:
        result = client.post(
            CLAIM_PATH,
            json=request.model_dump(mode="json"),
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/json",
            },
        )
        raw = result.content
        if (
            result.status_code != 200
            or not isinstance(raw, bytes)
            or len(raw) > MAX_API_RESPONSE_BYTES
            or "application/json" not in result.headers.get("content-type", "").lower()
        ):
            return _abstain("api_unavailable_or_invalid")
        return interpret_claim_reality_state(result.json(), request)
    except Exception:
        return _abstain("api_unavailable_or_invalid")


__all__ = [
    "AIClaimGateDecision", "check_claim_with_api",
    "interpret_claim_reality_state",
]
