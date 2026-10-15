"""Step250 explicit on-demand, read-only live-to-history reconciliation.

No nested FastAPI self-HTTP: original-source claim verification executes once
through the existing server-owned assurance pipeline. We use the Step246 pure
bounded comparison and Step248 keyed full-chain verification, twice, to refuse
concurrent changes without holding a SQLite write lock over network I/O.
"""
from __future__ import annotations

import json
import os

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.temporal_recheck import (
    TemporalRecheckRequest, TemporalRecheckResponse, TemporalRecheckEvidence,
)
from backend.app.api.pilot_auth import pilot_runtime_configuration
from backend.app.integrations.cited_answer_client import interpret_cited_answer
from backend.app.integrations.source_history import (
    InvalidHistory, operator_readonly_history_configuration,
)
from backend.app.integrations.source_timeline import latest_timeline_answer
from backend.app.integrations.source_recheck import reconcile_observations
from backend.app.services.original_source_answer_service import answer_original_source_claim


def _abstain(req: TemporalRecheckRequest, reason: str) -> TemporalRecheckResponse:
    return TemporalRecheckResponse(
        outcome="abstain", reason=reason,
        root_record_id=req.root_record_id,
        request_binding_sha256=claim_request_binding_sha256(req.claim),
    )


def reconcile_historical_reality_state(
    request: TemporalRecheckRequest,
) -> TemporalRecheckResponse:
    """Opt-in pilot only; fresh source I/O is explicitly authorized per request."""
    if os.environ.get("ARL_TEMPORAL_RECHECK_API_ENABLED") != "1":
        return _abstain(request, "reconciliation_not_enabled")
    try:
        enabled, token = pilot_runtime_configuration()
        allowed = json.loads(os.environ.get("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", ""))
        if (
            enabled is not True or token is None or type(allowed) is not list
            or request.claim.source_uri not in allowed
        ):
            return _abstain(request, "history_unavailable_or_invalid")
        path, key = operator_readonly_history_configuration()
        previous_id, previous = latest_timeline_answer(
            path, key, request.root_record_id, request.claim, readonly=True,
        )
    except (InvalidHistory, ValueError, TypeError, OSError, KeyError, AttributeError):
        return _abstain(request, "history_unavailable_or_invalid")

    try:
        # One true original-source read. The existing server pipeline selects
        # the original-source quote and enforces all claim and freshness gates.
        server_answer = answer_original_source_claim(request.claim)
        current = interpret_cited_answer(
            server_answer.model_dump(mode="json"), request.claim,
        )
        compared = reconcile_observations(request.claim, previous, current)
        if compared.status == "abstain" or compared.current is None or compared.previous is None:
            return _abstain(request, "fresh_evidence_unavailable_or_ambiguous")
        # Re-open complete timeline to detect a concurrent append or corruption.
        # No write transaction, source fetch or schema creation occurs here.
        latest_id, checked_previous = latest_timeline_answer(
            path, key, request.root_record_id, request.claim, readonly=True,
        )
        if (
            latest_id != previous_id or checked_previous != previous
        ):
            return _abstain(request, "timeline_changed_during_recheck")
        prior, fresh = compared.previous, compared.current
        return TemporalRecheckResponse(
            outcome="bounded_reconciliation",
            reason="fresh_original_source_compared_to_historical",
            request_binding_sha256=claim_request_binding_sha256(request.claim),
            root_record_id=request.root_record_id,
            baseline_record_id=previous_id,
            change_status=compared.status,
            previous=TemporalRecheckEvidence(
                source_quote_sha256=prior.source_quote_sha256,
                source_capture_sha256=prior.source_capture_sha256,
                source_capture_observed_at=prior.source_capture_observed_at,
                decision=compared.previous_decision,
            ),
            current=TemporalRecheckEvidence(
                source_quote_sha256=fresh.source_quote_sha256,
                source_capture_sha256=fresh.source_capture_sha256,
                source_capture_observed_at=fresh.source_capture_observed_at,
                decision=compared.current_decision,
            ),
            may_use_current_as_bounded_evidence=compared.may_use_current_as_bounded_evidence,
        )
    except (InvalidHistory, ValueError, TypeError, OSError,
            KeyError, AttributeError, OverflowError):
        # No saved/source data, exception details or partial receipts returned.
        return _abstain(request, "timeline_changed_during_recheck")


__all__ = ["reconcile_historical_reality_state"]
