"""Step244 fail-closed application consumer of the authenticated two-origin answer API.

Application-supplied client MUST have a trusted transport (verified TLS to
the intended API, or intentional trusted local TestClient) and secure bearer
token management. No client-side network source retrieval or model inference.
Two observed source texts are not publisher signatures or factual truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Literal

from backend.app.api.two_origin_answer import (
    PAIR_ABSTAINED, PAIR_ALIGNED, PAIR_CONTRADICTED, PAIR_DISAGREEMENT,
    TwoOriginAnswerRequest, TwoOriginAnswerResponse, two_origin_binding_sha256,
)
from backend.app.integrations.ai_claim_gate import MAX_API_RESPONSE_BYTES
from backend.app.integrations.cited_answer_client import CitedSourceObservation
from backend.app.reality.claim_assertion_alignment import _parse_atomic, _relationship

TWO_ORIGIN_ANSWER_PATH = "/api/v1/reality-state/answer/compare"

@dataclass(frozen=True)
class ClientTwoOriginAnswer:
    """Trust-bounded pair response. Source citations are UNTRUSTED display data."""

    decision: Literal[
        "two_source_alignment", "two_source_contradiction",
        "source_disagreement", "abstain",
    ]
    answer_text: str
    reason_code: Literal[
        "two_source_aligned", "two_source_contradicted",
        "two_source_disagreement", "source_abstained",
        "invalid_source_receipt", "api_unavailable_or_invalid",
    ]
    request_binding_sha256: str
    citations: tuple[CitedSourceObservation, ...] = ()
    may_use_as_bounded_evidence: bool = False
    distinct_https_hostnames: bool = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    independently_owned_publishers_verified: Literal[False] = False
    neural_model_used: Literal[False] = False
    general_question_answering: Literal[False] = False


def _abstain(
    request: TwoOriginAnswerRequest, reason: str = "invalid_source_receipt",
) -> ClientTwoOriginAnswer:
    # Failure never returns one of a pair's source quotes, URLs, hashes or times.
    return ClientTwoOriginAnswer(
        decision="abstain", answer_text=PAIR_ABSTAINED,
        reason_code=reason,
        request_binding_sha256=two_origin_binding_sha256(request),
    )


def interpret_two_origin_answer(
    data: object, request: TwoOriginAnswerRequest, *,
    now: datetime | None = None,
) -> ClientTwoOriginAnswer:
    """Fail closed on a malformed, partial, misbound, stale or misclassified pair.

    This guards against programming/integration and untrusted-intermediary
    errors; unkeyed SHA256 hashes are NOT origin authentication or signatures.
    A hostile server can forge content, so the caller MUST authenticate API TLS.
    """
    if not isinstance(request, TwoOriginAnswerRequest):
        raise TypeError("request must be a validated TwoOriginAnswerRequest")
    if type(data) is not dict:
        return _abstain(request)
    try:
        # Explicit JSON literal booleans, NOT Pydantic's possible type coercion.
        for name in (
            "factual_truth_verified", "publisher_authorship_verified",
            "independently_owned_publishers_verified", "neural_model_used",
            "general_question_answering",
        ):
            if type(data.get(name)) is not bool or data[name] is not False:
                return _abstain(request)
        for name in ("may_use_as_bounded_evidence", "distinct_https_hostnames"):
            if type(data.get(name)) is not bool:
                return _abstain(request)
        if type(data.get("source_observation_count")) is not int:
            return _abstain(request)

        parsed = TwoOriginAnswerResponse.model_validate(data)
        if parsed.request_binding_sha256 != two_origin_binding_sha256(request):
            return _abstain(request)
        if parsed.outcome == "abstain":
            if (
                parsed.answer_text != PAIR_ABSTAINED
                or parsed.reason_code != "source_evidence_incomplete"
                or parsed.citations != []
                or parsed.source_observation_count != 0
                or parsed.distinct_https_hostnames is not False
                or parsed.may_use_as_bounded_evidence is not False
            ):
                return _abstain(request)
            return _abstain(request, "source_abstained")

        outcomes = {
            "two_source_alignment": (
                "two_source_aligned", PAIR_ALIGNED, True,
                ("aligned", "aligned"),
            ),
            "two_source_contradiction": (
                "two_source_contradicted", PAIR_CONTRADICTED, False,
                ("contradicted", "contradicted"),
            ),
            "source_disagreement": (
                "two_source_disagreement", PAIR_DISAGREEMENT, False, None,
            ),
        }
        contract = outcomes.get(parsed.outcome)
        if contract is None:
            return _abstain(request)
        reason, text, permitted, relationships = contract
        if (
            parsed.reason_code != reason
            or parsed.answer_text != text
            or parsed.may_use_as_bounded_evidence is not permitted
            or parsed.distinct_https_hostnames is not True
            or parsed.source_observation_count != 2
            or len(parsed.citations) != 2
        ):
            return _abstain(request)
        current = datetime.now(timezone.utc) if now is None else now
        if current.tzinfo is None:
            return _abstain(request)
        parsed_claim = _parse_atomic(request.claim_text)
        if parsed_claim is None:
            return _abstain(request)
        safe_citations: list[CitedSourceObservation] = []
        observed_relations: list[str] = []
        for position, citation in enumerate(parsed.citations):
            quote = citation.original_source_quote
            if (
                citation.source_uri != request.source_uris[position]
                or quote != quote.strip()
                or any(character in quote for character in ("\n", "\r", "\x00"))
                or sha256(quote.encode("utf-8")).hexdigest()
                    != citation.source_quote_sha256
                or not citation.source_capture_observed_at.endswith("Z")
            ):
                return _abstain(request)
            seen = datetime.fromisoformat(
                citation.source_capture_observed_at.replace("Z", "+00:00")
            )
            if (
                seen.tzinfo is None
                or seen > current + timedelta(seconds=30)
                or seen < current - timedelta(
                    seconds=request.freshness_max_age_seconds
                )
            ):
                return _abstain(request)
            relationship = _relationship(parsed_claim, _parse_atomic(quote))
            if relationship not in ("aligned", "contradicted"):
                return _abstain(request)
            observed_relations.append(relationship)
            safe_citations.append(CitedSourceObservation(
                source_uri=citation.source_uri,
                original_source_quote=quote,
                source_quote_sha256=citation.source_quote_sha256,
                source_capture_sha256=citation.source_capture_sha256,
                source_capture_observed_at=citation.source_capture_observed_at,
            ))
        if relationships is not None:
            if tuple(observed_relations) != relationships:
                return _abstain(request)
        elif set(observed_relations) != {"aligned", "contradicted"}:
            return _abstain(request)
        return ClientTwoOriginAnswer(
            decision=parsed.outcome, answer_text=text,
            reason_code=reason,
            request_binding_sha256=two_origin_binding_sha256(request),
            citations=tuple(safe_citations),
            may_use_as_bounded_evidence=permitted,
            distinct_https_hostnames=True,
        )
    except (TypeError, ValueError, OverflowError, AttributeError):
        return _abstain(request)


def check_two_origin_answer_with_api(
    client: Any, token: str, request: TwoOriginAnswerRequest,
) -> ClientTwoOriginAnswer:
    """One authenticated API POST; never fetch publisher URLs in this client."""
    if not isinstance(request, TwoOriginAnswerRequest):
        raise TypeError("request must be a validated TwoOriginAnswerRequest")
    if (
        not isinstance(token, str)
        or not token.isascii()
        or not 32 <= len(token) <= 256
        or any(ord(c) < 33 or ord(c) > 126 for c in token)
    ):
        return _abstain(request, "api_unavailable_or_invalid")
    try:
        response = client.post(
            TWO_ORIGIN_ANSWER_PATH,
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
            or response.headers.get("content-type", "").split(";")[0].strip().lower()
                != "application/json"
        ):
            return _abstain(request, "api_unavailable_or_invalid")
        return interpret_two_origin_answer(response.json(), request)
    except Exception:
        # Neither a token, source quote, nor an exception body is ever leaked.
        return _abstain(request, "api_unavailable_or_invalid")


__all__ = [
    "ClientTwoOriginAnswer", "TWO_ORIGIN_ANSWER_PATH",
    "interpret_two_origin_answer", "check_two_origin_answer_with_api",
]
