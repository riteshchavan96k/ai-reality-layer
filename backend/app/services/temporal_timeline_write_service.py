"""Step251 privileged, opt-in application lifecycle source storage service.

No sources chosen by the server, no nested FastAPI self-HTTP, no autonomous
retries. Authorization occurs in pilot middleware before invoking this module.
"""
from __future__ import annotations

import json
import os

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.pilot_auth import (
    pilot_runtime_configuration, timeline_writer_configuration,
)
from backend.app.api.temporal_timeline_write import (
    TimelineCreateRequest, TimelineAppendRequest, TimelineWriteResponse,
)
from backend.app.integrations.cited_answer_client import interpret_cited_answer
from backend.app.integrations.source_history import (
    InvalidHistory, operator_history_configuration,
    operator_readonly_history_configuration,
)
from backend.app.integrations.source_timeline import latest_timeline_answer
from backend.app.integrations.source_timeline_writes import (
    lookup_operation, commit_create, commit_append,
)
from backend.app.services.original_source_answer_service import answer_original_source_claim


def _abstain(req: TimelineCreateRequest, reason: str) -> TimelineWriteResponse:
    return TimelineWriteResponse(
        outcome="abstain", reason=reason,
        operation_id=req.operation_id,
        request_binding_sha256=claim_request_binding_sha256(req.claim),
    )


def _permitted(req: TimelineCreateRequest) -> bool:
    if os.environ.get("ARL_TIMELINE_WRITE_API_ENABLED") != "1":
        return False
    try:
        enabled, _ = pilot_runtime_configuration()
        writer = timeline_writer_configuration()
        sources = json.loads(os.environ.get("ARL_INDEPENDENT_SOURCE_ALLOWED_URLS", ""))
        return (
            enabled and writer is not None and type(sources) is list
            and req.claim.source_uri in sources
        )
    except (ValueError, TypeError, UnicodeError):
        return False


def _capture(req: TimelineCreateRequest):
    # Never save an unverified publisher response or a caller-supplied quote.
    answer = answer_original_source_claim(req.claim)
    verified = interpret_cited_answer(answer.model_dump(mode="json"), req.claim)
    if verified.decision not in ("bounded_source_support", "bounded_source_contradiction"):
        raise InvalidHistory("fresh original-source evidence unavailable")
    return verified


def create_historical_timeline(req: TimelineCreateRequest) -> TimelineWriteResponse:
    if not _permitted(req):
        return _abstain(req, "write_not_available")
    try:
        path, key = operator_history_configuration()
        cached = lookup_operation(path, key, req.operation_id, req.claim, "create")
        if cached is not None:
            return TimelineWriteResponse.model_validate(cached)
        fresh = _capture(req)
        result = commit_create(path, key, req.operation_id, req.claim, fresh)
        return TimelineWriteResponse.model_validate(result)
    except (InvalidHistory, ValueError, TypeError, OSError, OverflowError, AttributeError):
        return _abstain(req, "history_unavailable_or_invalid")


def append_historical_timeline(req: TimelineAppendRequest) -> TimelineWriteResponse:
    if not _permitted(req):
        return _abstain(req, "write_not_available")
    try:
        path, key = operator_readonly_history_configuration()
        cached = lookup_operation(
            path, key, req.operation_id, req.claim, "append",
            req.root_record_id, req.expected_latest_record_id,
        )
        if cached is not None:
            return TimelineWriteResponse.model_validate(cached)
        latest_id, _ = latest_timeline_answer(
            path, key, req.root_record_id, req.claim, readonly=True,
        )
        if latest_id != req.expected_latest_record_id:
            return _abstain(req, "timeline_stale_or_conflicting")
        fresh = _capture(req)
        result = commit_append(
            path, key, req.operation_id, req.claim,
            req.root_record_id, req.expected_latest_record_id, fresh,
        )
        return TimelineWriteResponse.model_validate(result)
    except (InvalidHistory, ValueError, TypeError, OSError, OverflowError, AttributeError):
        return _abstain(req, "history_unavailable_or_invalid")


__all__ = ["create_historical_timeline", "append_historical_timeline"]
