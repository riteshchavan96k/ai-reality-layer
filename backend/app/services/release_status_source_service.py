"""One original HTTPS source capture bound to a narrow release type assertion."""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import re
from backend.app.api.release_status import (
    ReleaseStatusSourceRequest,ReleaseStatusSourceResponse,release_status_binding
)
from backend.app.api.release_date import ReleaseDateSourceCitation
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.reality.independent_source_text_assurance import MAX_INDEPENDENT_SOURCE_TEXT_CHARS
from backend.app.reality.release_status_policy import status_question_valid,select_release_type_unit

def observe_release_status(request: ReleaseStatusSourceRequest) -> ReleaseStatusSourceResponse:
    if not isinstance(request,ReleaseStatusSourceRequest):
        raise TypeError("invalid_status_request")
    binding=release_status_binding(request)
    def abstain(reason: str) -> ReleaseStatusSourceResponse:
        return ReleaseStatusSourceResponse(
            outcome="abstain",reason_code=reason,request_binding_sha256=binding
        )
    if not status_question_valid(request.question,request.entity,request.source_uri):
        return abstain("invalid_question_or_identity")
    try:
        reader=OrchestrationDependencies.default().independent_source_text_assurance._reader
    except (ValueError,TypeError):
        return abstain("source_unavailable")
    if not isinstance(reader,AllowlistedHttpsSourceReader):
        return abstain("source_unavailable")
    if request.source_uri not in reader._allowed:
        return abstain("source_not_operator_allowed")
    try:
        captured=reader(request.source_uri)
    except Exception:
        return abstain("source_unavailable")
    if type(captured) is not dict or captured.get("uri")!=request.source_uri:
        return abstain("source_capture_invalid")
    body=captured.get("content")
    digest=captured.get("capture_sha256")
    observed_at=captured.get("capture_observed_at")
    quoted=captured.get("observed_quote_unit_sha256")
    if (
        type(body) is not str or not 0<len(body)<=MAX_INDEPENDENT_SOURCE_TEXT_CHARS
        or type(digest) is not str or re.fullmatch(r"[a-f0-9]{64}",digest) is None
        or type(observed_at) is not str or not 1<=len(observed_at)<=64
        or not observed_at.endswith("Z")
        or type(quoted) not in (list,tuple) or len(quoted)>10000
        or any(type(h) is not str or re.fullmatch(r"[a-f0-9]{64}",h) is None for h in quoted)
    ):
        return abstain("source_capture_invalid")
    try:
        seen=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        now=datetime.now(timezone.utc)
        if seen.tzinfo is None or seen>now+timedelta(seconds=30) or seen<now-timedelta(
            seconds=request.freshness_max_age_seconds
        ):
            return abstain("source_capture_invalid")
    except (ValueError,TypeError,OverflowError):
        return abstain("source_capture_invalid")
    unit=select_release_type_unit(body,request.entity)
    if unit is None:
        return abstain("source_ambiguous_or_unverified")
    unit_digest=sha256(unit.encode("utf-8")).hexdigest()
    if unit_digest in quoted:
        return abstain("source_ambiguous_or_unverified")
    return ReleaseStatusSourceResponse(
        outcome="source_status_observed",reason_code="stable_release_statement_observed",
        request_binding_sha256=binding,citation=ReleaseDateSourceCitation(
            source_uri=request.source_uri,original_source_quote=unit,
            source_quote_sha256=unit_digest,source_capture_sha256=digest,
            source_capture_observed_at=observed_at,
        ),original_source_observed=True
    )

__all__=["observe_release_status"]
