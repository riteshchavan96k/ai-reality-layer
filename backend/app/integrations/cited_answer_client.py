"""Fail-closed application client for Step 241's authenticated cited answer API.

A trustworthy transport is the caller's responsibility. A SHA-256 receipt is
not a signature or evidence of publisher authorship. Excerpts are untrusted
publisher text, NEVER executable instructions or safe HTML.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Literal

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_answer import BoundedOriginalSourceAnswerResponse
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.ai_claim_gate import MAX_API_RESPONSE_BYTES

ANSWER_PATH = "/api/v1/reality-state/answer"
ALIGNED = (
    "The observed original-source statement aligns with the submitted claim "
    "under a bounded textual verification policy."
)
CONTRADICTED = (
    "The observed original-source statement contradicts the submitted claim "
    "under a bounded textual verification policy."
)
ABSTAINED = "The available original-source evidence is insufficient for a bounded answer."


@dataclass(frozen=True)
class CitedSourceObservation:
    """Immutable, untrusted original-source quote and one capture's audit fields."""

    source_uri: str
    original_source_quote: str
    source_quote_sha256: str
    source_capture_sha256: str
    source_capture_observed_at: str


@dataclass(frozen=True)
class ClientCitedAnswer:
    decision: Literal["bounded_source_support", "bounded_source_contradiction", "abstain"]
    answer_text: str
    reason_code: Literal[
        "source_aligned", "source_contradicted", "source_abstained",
        "api_unavailable_or_invalid", "invalid_source_receipt",
    ]
    request_binding_sha256: str
    citation: CitedSourceObservation | None = None
    may_use_as_bounded_evidence: bool = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    neural_model_used: Literal[False] = False
    general_question_answering: Literal[False] = False


def _abstain(request: OriginalSourceClaimRequest, reason: str) -> ClientCitedAnswer:
    return ClientCitedAnswer(
        decision="abstain", answer_text=ABSTAINED,
        reason_code=reason, request_binding_sha256=claim_request_binding_sha256(request),
    )


def interpret_cited_answer(
    data: object,
    request: OriginalSourceClaimRequest,
    *,
    now: datetime | None = None,
) -> ClientCitedAnswer:
    """Validate all source attribution before exposing a quote to AI applications.

    This rejects an inconsistent intermediary response, but cannot prove that
    the server/transport or publisher are honest. Only use with an authenticated,
    TLS-verified API (or an intentionally local, trusted integration test).
    """
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be validated before interpreting a response")
    if not isinstance(data, dict):
        return _abstain(request, "api_unavailable_or_invalid")
    try:
        # Prevent permissive Pydantic coercion of numeric 0 into an epistemic
        # ceiling that must be the actual JSON boolean false.
        for flag in (
            "factual_truth_verified", "publisher_authorship_verified",
            "neural_model_used", "general_question_answering",
        ):
            if type(data.get(flag)) is not bool or data[flag] is not False:
                return _abstain(request, "invalid_source_receipt")
        if type(data.get("original_source_observed")) is not bool:
            return _abstain(request, "invalid_source_receipt")
        parsed = BoundedOriginalSourceAnswerResponse.model_validate(data)
        if parsed.request_binding_sha256 != claim_request_binding_sha256(request):
            return _abstain(request, "invalid_source_receipt")
        if parsed.outcome == "abstain":
            if (
                parsed.answer_text != ABSTAINED or parsed.citation is not None
                or parsed.original_source_observed is not False
            ):
                return _abstain(request, "invalid_source_receipt")
            return _abstain(request, "source_abstained")

        if parsed.outcome not in ("bounded_source_support", "bounded_source_contradiction"):
            return _abstain(request, "invalid_source_receipt")
        if parsed.answer_text != (
            ALIGNED if parsed.outcome == "bounded_source_support" else CONTRADICTED
        ) or parsed.original_source_observed is not True:
            return _abstain(request, "invalid_source_receipt")
        c = parsed.citation
        if c is None:
            return _abstain(request, "invalid_source_receipt")
        quote = c.original_source_quote
        if (
            c.source_uri != request.source_uri
            or quote != quote.strip()
            or any(character in quote for character in ("\n", "\r", "\x00"))
            or sha256(quote.encode("utf-8")).hexdigest() != c.source_quote_sha256
            or not c.source_capture_observed_at.endswith("Z")
        ):
            return _abstain(request, "invalid_source_receipt")

        seen = datetime.fromisoformat(
            c.source_capture_observed_at.replace("Z", "+00:00")
        )
        current = datetime.now(timezone.utc) if now is None else now
        if (
            seen.tzinfo is None or current.tzinfo is None
            or seen > current + timedelta(seconds=30)
            or seen < current - timedelta(seconds=request.freshness_max_age_seconds)
        ):
            return _abstain(request, "invalid_source_receipt")
        citation = CitedSourceObservation(
            source_uri=c.source_uri,
            original_source_quote=quote,
            source_quote_sha256=c.source_quote_sha256,
            source_capture_sha256=c.source_capture_sha256,
            source_capture_observed_at=c.source_capture_observed_at,
        )
        supported = parsed.outcome == "bounded_source_support"
        return ClientCitedAnswer(
            decision=parsed.outcome,
            answer_text=ALIGNED if supported else CONTRADICTED,
            reason_code="source_aligned" if supported else "source_contradicted",
            request_binding_sha256=claim_request_binding_sha256(request),
            citation=citation,
            may_use_as_bounded_evidence=supported,
        )
    except (TypeError, ValueError, OverflowError, AttributeError):
        return _abstain(request, "invalid_source_receipt")


def check_cited_answer_with_api(
    client: Any,
    token: str,
    request: OriginalSourceClaimRequest,
) -> ClientCitedAnswer:
    """One authenticated POST; fail closed on all transport and payload errors.

    The transport must not send bearer secrets to an untrusted host. Do not
    interpolate the returned quote into an LLM's system instructions or HTML.
    """
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be a validated OriginalSourceClaimRequest")
    if (
        not isinstance(token, str) or not token.isascii()
        or not 32 <= len(token) <= 256
        or any(ord(c) < 33 or ord(c) > 126 for c in token)
    ):
        return _abstain(request, "api_unavailable_or_invalid")
    try:
        response = client.post(
            ANSWER_PATH,
            json=request.model_dump(mode="json"),
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/json",
            },
        )
        raw = response.content
        if (
            response.status_code != 200
            or not isinstance(raw, bytes)
            or len(raw) > MAX_API_RESPONSE_BYTES
            or "application/json" not in response.headers.get("content-type", "").lower()
        ):
            return _abstain(request, "api_unavailable_or_invalid")
        return interpret_cited_answer(response.json(), request)
    except Exception:
        # No source body, untrusted exception or token is logged or returned.
        return _abstain(request, "api_unavailable_or_invalid")


__all__ = [
    "CitedSourceObservation", "ClientCitedAnswer", "ANSWER_PATH",
    "interpret_cited_answer", "check_cited_answer_with_api",
]
