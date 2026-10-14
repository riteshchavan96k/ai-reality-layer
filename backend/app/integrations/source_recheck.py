"""Step246 explicit recheck of a previously consumed bounded original-source claim.

No scheduling, historical archive, publisher signatures, real-world truth or
automatic source discovery. A caller-provided historical ClientCitedAnswer is
NOT cryptographically authenticated; this API only guards its structure and
freshly re-verifies the exact original-source request using a trusted client.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import re
from typing import Any, Literal

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import (
    ALIGNED, CONTRADICTED, CitedSourceObservation, ClientCitedAnswer,
    check_cited_answer_with_api,
)
from backend.app.reality.claim_assertion_alignment import _parse_atomic, _relationship

HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
RECHECK_ABSTAINED = (
    "A historical and fresh original-source observation could not both be "
    "validated for a bounded recheck."
)

@dataclass(frozen=True)
class SourceRecheck:
    """An explicitly requested observation comparison, NOT historical attestation."""

    status: Literal[
        "capture_unchanged", "capture_changed_statement_unchanged",
        "bounded_statement_changed", "abstain",
    ]
    answer_text: str
    request_binding_sha256: str
    previous: CitedSourceObservation | None = None
    current: CitedSourceObservation | None = None
    previous_decision: str | None = None
    current_decision: str | None = None
    may_use_current_as_bounded_evidence: bool = False
    factual_truth_verified: Literal[False] = False
    publisher_authorship_verified: Literal[False] = False
    historical_receipt_authenticated: Literal[False] = False
    independent_publisher_ownership_verified: Literal[False] = False
    automatic_monitoring_enabled: Literal[False] = False


def _abstain(request: OriginalSourceClaimRequest) -> SourceRecheck:
    return SourceRecheck(
        status="abstain",
        answer_text=RECHECK_ABSTAINED,
        request_binding_sha256=claim_request_binding_sha256(request),
    )


def _validated_observation(
    prior: ClientCitedAnswer, request: OriginalSourceClaimRequest,
    current: datetime,
) -> tuple[CitedSourceObservation, datetime] | None:
    """Structural consistency, not evidence that a historical claim was honest."""
    if type(prior) is not ClientCitedAnswer:
        return None
    if any(
        type(getattr(prior, key, None)) is not bool
        or getattr(prior, key) is not False
        for key in (
            "factual_truth_verified", "publisher_authorship_verified",
            "neural_model_used", "general_question_answering",
        )
    ):
        return None
    if (
        prior.decision not in ("bounded_source_support", "bounded_source_contradiction")
        or prior.request_binding_sha256 != claim_request_binding_sha256(request)
        or prior.reason_code != (
            "source_aligned" if prior.decision == "bounded_source_support"
            else "source_contradicted"
        )
        or prior.answer_text != (
            ALIGNED if prior.decision == "bounded_source_support" else CONTRADICTED
        )
        or type(prior.may_use_as_bounded_evidence) is not bool
        or prior.may_use_as_bounded_evidence is not (
            prior.decision == "bounded_source_support"
        )
        or type(prior.citation) is not CitedSourceObservation
    ):
        return None
    c = prior.citation
    if (
        type(c.source_uri) is not str
        or c.source_uri != request.source_uri
        or type(c.original_source_quote) is not str
        or c.original_source_quote != c.original_source_quote.strip()
        or not 0 < len(c.original_source_quote) <= 500
        or any(x in c.original_source_quote for x in ("\n", "\r", "\x00"))
        or type(c.source_quote_sha256) is not str
        or HEX_SHA256.fullmatch(c.source_quote_sha256) is None
        or sha256(c.original_source_quote.encode("utf-8")).hexdigest() != c.source_quote_sha256
        or type(c.source_capture_sha256) is not str
        or HEX_SHA256.fullmatch(c.source_capture_sha256) is None
        or type(c.source_capture_observed_at) is not str
        or not c.source_capture_observed_at.endswith("Z")
    ):
        return None
    claim = _parse_atomic(request.claim_text)
    quote = _parse_atomic(c.original_source_quote)
    relationship = _relationship(claim, quote)
    if relationship != (
        "aligned" if prior.decision == "bounded_source_support" else "contradicted"
    ):
        return None
    try:
        observed = datetime.fromisoformat(
            c.source_capture_observed_at.replace("Z", "+00:00")
        )
        if observed.tzinfo is None or observed > current + timedelta(seconds=30):
            return None
        return c, observed
    except (ValueError, OverflowError):
        return None


def recheck_cited_answer_with_api(
    client: Any,
    token: str,
    request: OriginalSourceClaimRequest,
    previous: ClientCitedAnswer,
    *,
    now: datetime | None = None,
) -> SourceRecheck:
    """At most ONE new authenticated request; no source egress for bad baseline.

    Previous observation can be older than the freshness limit because it
    is only a comparison baseline, NEVER trusted as currently fresh.
    The present observation MUST independently satisfy normal freshness.
    A no-change digest is an observation, not guaranteed publisher truth.
    """
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("a validated OriginalSourceClaimRequest is required")
    try:
        current_time = datetime.now(timezone.utc) if now is None else now
        if current_time.tzinfo is None:
            return _abstain(request)
        baseline = _validated_observation(previous, request, current_time)
        if baseline is None:
            return _abstain(request)
        current = check_cited_answer_with_api(client, token, request)
        refreshed = _validated_observation(current, request, current_time)
        if refreshed is None:
            return _abstain(request)
        old_citation, old_time = baseline
        new_citation, new_time = refreshed
        if new_time < old_time:
            return _abstain(request)
        unchanged_digest = old_citation.source_capture_sha256 == new_citation.source_capture_sha256
        unchanged_quote = (
            old_citation.source_quote_sha256 == new_citation.source_quote_sha256
            and previous.decision == current.decision
        )
        if unchanged_digest and not unchanged_quote:
            # The same raw captured bytes cannot support two different
            # source statements/decisions for the same canonical request.
            return _abstain(request)
        if unchanged_digest:
            status = "capture_unchanged"
            answer_text = "Two observations have the same source capture SHA-256."
        elif unchanged_quote:
            status = "capture_changed_statement_unchanged"
            answer_text = (
                "The source capture SHA-256 changed, but the bounded source "
                "statement and its claim relation remained unchanged."
            )
        else:
            status = "bounded_statement_changed"
            answer_text = (
                "A fresh bounded source statement or claim relation differs "
                "from the caller-held baseline observation."
            )
        return SourceRecheck(
            status=status, answer_text=answer_text,
            request_binding_sha256=claim_request_binding_sha256(request),
            previous=old_citation, current=new_citation,
            previous_decision=previous.decision, current_decision=current.decision,
            may_use_current_as_bounded_evidence=(
                current.decision == "bounded_source_support"
            ),
        )
    except (ValueError, OverflowError, TypeError, AttributeError):
        return _abstain(request)


__all__ = ["SourceRecheck", "recheck_cited_answer_with_api", "RECHECK_ABSTAINED"]
