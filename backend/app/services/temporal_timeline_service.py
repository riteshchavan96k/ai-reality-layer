"""Step249 read-only, opt-in API adapter for Step248 operator-held history.

This is a historical observation interface, NEVER an evidence freshness
upgrade, publisher-signed receipt, or network source reader. All database
checks remain the Step247/248 checks and run in a mode=ro SQLite connection.
"""
import json
import os

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.pilot_auth import pilot_runtime_configuration
from backend.app.api.temporal_timeline import TemporalTimelineRequest, TemporalTimelineResponse
from backend.app.integrations.source_history import (
    InvalidHistory, operator_readonly_history_configuration,
)
from backend.app.integrations.source_timeline import inspect_timeline


def _abstain(request: TemporalTimelineRequest, reason: str) -> TemporalTimelineResponse:
    return TemporalTimelineResponse(
        outcome="abstain", reason=reason,
        request_binding_sha256=claim_request_binding_sha256(request.claim),
        root_record_id=request.root_record_id,
        timeline=None,
    )


def historical_timeline_readonly(
    request: TemporalTimelineRequest,
) -> TemporalTimelineResponse:
    """One authorized local read only, with no source I/O and no DB writes."""
    if os.environ.get("ARL_TEMPORAL_HISTORY_API_ENABLED") != "1":
        return _abstain(request, "timeline_api_not_enabled")
    try:
        enabled, token = pilot_runtime_configuration()
        if enabled is not True or token is None:
            return _abstain(request, "timeline_api_not_enabled")
        allowed = json.loads(os.environ.get("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", ""))
        if (
            type(allowed) is not list
            or request.claim.source_uri not in allowed
        ):
            return _abstain(request, "history_unavailable_or_invalid")
        path, key = operator_readonly_history_configuration()
        data = inspect_timeline(
            path, key, request.root_record_id, request.claim, readonly=True,
        )
        return TemporalTimelineResponse(
            outcome="verified_historical_timeline",
            reason="operator_history_validated",
            request_binding_sha256=claim_request_binding_sha256(request.claim),
            root_record_id=request.root_record_id,
            timeline=data,
        )
    except (ValueError, TypeError, OSError, InvalidHistory, KeyError, AttributeError):
        # Never expose DB paths, publisher excerpts, MAC keys or exception text.
        return _abstain(request, "history_unavailable_or_invalid")


__all__ = ["historical_timeline_readonly"]
