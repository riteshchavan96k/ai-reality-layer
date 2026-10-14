"""Convert exactly one strict original-source Reality State into a cited answer.

No model execution, no independent extra source read, no open-domain
assertions, no natural-language paraphrasing of untrusted text. This is a
narrow, authenticated, independently source-observed answer renderer.
"""

from __future__ import annotations

from hashlib import sha256
import re
from typing import Any

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_answer import (
    BoundedOriginalSourceAnswerResponse,
    ObservedAnswerCitation,
)
from backend.app.api.original_source_claim import OriginalSourceClaimRequest, OriginalSourceClaimResponse
from backend.app.integrations.ai_claim_gate import interpret_claim_reality_state
from backend.app.services.original_source_claim_service import verify_original_source_claim

_HASH = re.compile(r"[0-9a-f]{64}")
ALIGNED = (
    "The observed original-source statement aligns with the submitted claim "
    "under a bounded textual verification policy."
)
CONTRADICTED = (
    "The observed original-source statement contradicts the submitted claim "
    "under a bounded textual verification policy."
)
ABSTAINED = "The available original-source evidence is insufficient for a bounded answer."


def _abstain(request: OriginalSourceClaimRequest) -> BoundedOriginalSourceAnswerResponse:
    """All failures suppress source URL, text, quote hashes and timestamps."""
    return BoundedOriginalSourceAnswerResponse(
        outcome="abstain", answer_text=ABSTAINED,
        request_binding_sha256=claim_request_binding_sha256(request),
        citation=None, original_source_observed=False,
    )


def render_original_source_answer(
    request: OriginalSourceClaimRequest,
    claim_response: OriginalSourceClaimResponse,
) -> BoundedOriginalSourceAnswerResponse:
    """Fail closed even when given a malformed or mixed in-memory result."""
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be a validated OriginalSourceClaimRequest")
    if not isinstance(claim_response, OriginalSourceClaimResponse):
        return _abstain(request)
    try:
        response = claim_response.model_dump(mode="json")
        original = interpret_claim_reality_state(response, request)
        if original.decision not in ("bounded_supported", "bounded_contradicted"):
            return _abstain(request)
        evidence = response.get("source_evidence")
        if not isinstance(evidence, dict) or set(evidence) != {
            "text", "text_sha256", "source_capture_sha256",
            "source_capture_observed_at",
        }:
            return _abstain(request)
        text, digest = evidence["text"], evidence["text_sha256"]
        if (
            type(text) is not str or not 0 < len(text) <= 500
            or text != text.strip()
            or any(c in text for c in ("\n", "\r", "\x00"))
            or type(digest) is not str or _HASH.fullmatch(digest) is None
            or sha256(text.encode("utf-8")).hexdigest() != digest
            or evidence["source_capture_sha256"] != original.capture_sha256
            or evidence["source_capture_observed_at"] != original.capture_observed_at
            or original.source_ref != request.source_uri
        ):
            return _abstain(request)
        citation = ObservedAnswerCitation(
            source_uri=request.source_uri,
            original_source_quote=text,
            source_quote_sha256=digest,
            source_capture_sha256=original.capture_sha256,
            source_capture_observed_at=original.capture_observed_at,
        )
        is_supported = original.decision == "bounded_supported"
        return BoundedOriginalSourceAnswerResponse(
            outcome=(
                "bounded_source_support" if is_supported
                else "bounded_source_contradiction"
            ),
            answer_text=ALIGNED if is_supported else CONTRADICTED,
            request_binding_sha256=claim_request_binding_sha256(request),
            citation=citation,
            original_source_observed=True,
        )
    except (TypeError, ValueError, KeyError, AttributeError):
        return _abstain(request)


def answer_original_source_claim(
    request: OriginalSourceClaimRequest,
) -> BoundedOriginalSourceAnswerResponse:
    """Exactly one original-source verification; no duplicated HTTP reads."""
    if not isinstance(request, OriginalSourceClaimRequest):
        raise TypeError("request must be validated")
    response = verify_original_source_claim(request)
    return render_original_source_answer(request, response)


__all__ = ["answer_original_source_claim", "render_original_source_answer"]
