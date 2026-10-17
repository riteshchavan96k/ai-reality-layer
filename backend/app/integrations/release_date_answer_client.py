"""Step253: model may extract a value, never certify source truth.

Trusted authenticated transport supplies ONE server-captured date field. The
model receives bounded question+source field only (no bearer or URL), and its
output must match an independently parsed original source date.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Literal

from backend.app.api.release_date import (
    ReleaseDateSourceRequest, ReleaseDateSourceResponse,
    ReleaseDateSourceCitation, release_date_binding,
)
from backend.app.reality.release_date_policy import (
    expected_question, parse_date, parse_release_date_label,
)

PATH = "/api/v1/reality-state/extract/release-date"
MAX_BYTES = 8192


@dataclass(frozen=True)
class EvidenceConditionedDateAnswer:
    outcome: Literal["bounded_source_date", "abstain"]
    reason_code: Literal[
        "source_date_matches_generation", "invalid_question_or_source",
        "source_unavailable_or_invalid", "generated_date_invalid_or_mismatched",
        "model_unavailable_or_invalid",
    ]
    answer_iso: str | None = None
    citation: ReleaseDateSourceCitation | None = None
    model_executed: bool = False
    may_use_as_bounded_evidence: bool = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    general_question_answering: Literal[False] = False
    externally_deployed: Literal[False] = False


def _refuse(reason: str, model_called: bool = False) -> EvidenceConditionedDateAnswer:
    return EvidenceConditionedDateAnswer(
        "abstain", reason, model_executed=model_called
    )


def _verified_receipt(raw: object, request: ReleaseDateSourceRequest) -> tuple[
    ReleaseDateSourceCitation, datetime
] | None:
    if type(raw) is not dict:
        return None
    for k in (
        "factual_truth_verified", "publisher_authorship_verified",
        "model_used_for_source_verification", "general_question_answering",
    ):
        if type(raw.get(k)) is not bool or raw[k] is not False:
            return None
    if type(raw.get("original_source_observed")) is not bool:
        return None
    try:
        reply = ReleaseDateSourceResponse.model_validate(raw)
        if (
            reply.request_binding_sha256 != release_date_binding(request)
            or reply.outcome != "source_date_observed"
            or reply.reason_code != "unique_release_date_observed"
            or reply.original_source_observed is not True
            or reply.citation is None
        ):
            return None
        cite = reply.citation
        if (
            cite.source_uri != request.source_uri
            or cite.original_source_quote != cite.original_source_quote.strip()
            or sha256(cite.original_source_quote.encode("utf-8")).hexdigest()
               != cite.source_quote_sha256
        ):
            return None
        actual_date = parse_release_date_label(cite.original_source_quote)
        if actual_date is None:
            return None
        seen = datetime.fromisoformat(
            cite.source_capture_observed_at.replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        if (
            seen.tzinfo is None or seen > now + timedelta(seconds=30)
            or seen < now - timedelta(seconds=request.freshness_max_age_seconds)
            or actual_date > now.date()
        ):
            return None
        return cite, datetime.combine(
            actual_date, datetime.min.time(), tzinfo=timezone.utc
        )
    except (TypeError, ValueError, OverflowError, AttributeError):
        return None


def check_release_date_with_model(
    client: Any, token: str, request: ReleaseDateSourceRequest, model: Any
) -> EvidenceConditionedDateAnswer:
    if not isinstance(request, ReleaseDateSourceRequest) or not expected_question(
        request.question, request.entity, request.source_uri
    ):
        return _refuse("invalid_question_or_source")
    if (
        type(token) is not str or not token.isascii() or not 32 <= len(token) <= 256
        or any(ord(c) < 33 or ord(c) > 126 for c in token)
    ):
        return _refuse("source_unavailable_or_invalid")
    if not callable(getattr(model, "extract_date", None)):
        return _refuse("model_unavailable_or_invalid")
    try:
        response = client.post(
            PATH, json=request.model_dump(mode="json"), headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/json",
            },
        )
        raw = response.content
        if (
            response.status_code != 200 or type(raw) is not bytes
            or len(raw) > MAX_BYTES
            or "application/json" not in response.headers.get("content-type", "").lower()
        ):
            return _refuse("source_unavailable_or_invalid")
        valid = _verified_receipt(response.json(), request)
    except Exception:
        return _refuse("source_unavailable_or_invalid")
    if valid is None:
        return _refuse("source_unavailable_or_invalid")
    citation, observed_calendar_date = valid
    try:
        generated = model.extract_date(
            request.question, citation.original_source_quote
        )
    except Exception:
        return _refuse("model_unavailable_or_invalid", model_called=True)
    generated_date = parse_date(generated)
    if generated_date is None or generated_date != observed_calendar_date.date():
        return _refuse("generated_date_invalid_or_mismatched", model_called=True)
    return EvidenceConditionedDateAnswer(
        outcome="bounded_source_date",
        reason_code="source_date_matches_generation",
        answer_iso=generated_date.isoformat(),
        citation=citation,
        model_executed=True,
        may_use_as_bounded_evidence=True,
    )


__all__ = ["PATH", "EvidenceConditionedDateAnswer", "check_release_date_with_model"]
