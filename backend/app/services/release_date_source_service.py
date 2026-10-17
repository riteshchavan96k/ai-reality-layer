"""Step253 server-only one-capture release-date evidence source.

No model may drive URL choice, heading matching, quote selection, or source
metadata. Error/ambiguity exits never include a partial source or answer.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import re

from backend.app.api.release_date import (
    ReleaseDateSourceRequest, ReleaseDateSourceResponse,
    ReleaseDateSourceCitation, release_date_binding,
)
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.reality.independent_source_text_assurance import MAX_INDEPENDENT_SOURCE_TEXT_CHARS
from backend.app.reality.release_date_policy import expected_question, select_date_unit


def observe_release_date(request: ReleaseDateSourceRequest) -> ReleaseDateSourceResponse:
    if not isinstance(request, ReleaseDateSourceRequest):
        raise TypeError("invalid_validated_request")
    binding = release_date_binding(request)

    def abstain(reason: str) -> ReleaseDateSourceResponse:
        return ReleaseDateSourceResponse(
            outcome="abstain", reason_code=reason, request_binding_sha256=binding,
        )

    if not expected_question(request.question, request.entity, request.source_uri):
        return abstain("invalid_question_or_identity")
    try:
        reader = OrchestrationDependencies.default().independent_source_text_assurance._reader
    except (TypeError, ValueError):
        return abstain("source_unavailable")
    if not isinstance(reader, AllowlistedHttpsSourceReader):
        return abstain("source_unavailable")
    if request.source_uri not in reader._allowed:
        return abstain("source_not_operator_allowed")

    try:
        captured = reader(request.source_uri)
    except Exception:
        return abstain("source_unavailable")
    if not isinstance(captured, dict) or captured.get("uri") != request.source_uri:
        return abstain("source_capture_invalid")
    body = captured.get("content")
    digest = captured.get("capture_sha256")
    observed_at = captured.get("capture_observed_at")
    quote_hashes = captured.get("observed_quote_unit_sha256")
    if (
        type(body) is not str or not 0 < len(body) <= MAX_INDEPENDENT_SOURCE_TEXT_CHARS
        or type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or type(observed_at) is not str or not 0 < len(observed_at) <= 64
        or not observed_at.endswith("Z")
        or type(quote_hashes) not in (tuple, list)
        or len(quote_hashes) > 10000
        or any(type(h) is not str or re.fullmatch(r"[0-9a-f]{64}", h) is None
               for h in quote_hashes)
    ):
        return abstain("source_capture_invalid")
    try:
        seen = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if (
            seen.tzinfo is None or seen > now + timedelta(seconds=30)
            or seen < now - timedelta(seconds=request.freshness_max_age_seconds)
        ):
            return abstain("source_capture_invalid")
    except (OverflowError, TypeError, ValueError):
        return abstain("source_capture_invalid")
    selected = select_date_unit(body, request.entity)
    if selected is None:
        return abstain("source_ambiguous_or_unverified")
    unit, date = selected
    quote_sha = sha256(unit.encode("utf-8")).hexdigest()
    if quote_sha in quote_hashes or date > now.date():
        return abstain("source_ambiguous_or_unverified")
    return ReleaseDateSourceResponse(
        outcome="source_date_observed",
        reason_code="unique_release_date_observed",
        request_binding_sha256=binding,
        citation=ReleaseDateSourceCitation(
            source_uri=request.source_uri,
            original_source_quote=unit,
            source_quote_sha256=quote_sha,
            source_capture_sha256=digest,
            source_capture_observed_at=observed_at,
        ),
        original_source_observed=True,
    )


__all__ = ["observe_release_date"]
