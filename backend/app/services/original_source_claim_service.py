"""Claim -> one original-source capture -> bounded Reality State.

The source URL is only an operator-allowlisted *candidate*. A single
independently captured document is reused without a second network read,
so excerpt selection and provenance cannot silently describe different pages.
No publisher/authorship, semantic or factual-truth certification is implied.
"""

from dataclasses import replace
from hashlib import sha256
import re

from backend.app.api.original_source_claim import (
    OriginalSourceClaimRequest,
    OriginalSourceClaimResponse,
)
from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.orchestrator.orchestrator import build_reality_state_from_evidence
from backend.app.reality.allowlisted_https_source_reader import AllowlistedHttpsSourceReader
from backend.app.reality.claim_assertion_alignment import _parse_atomic, _relationship
from backend.app.reality.independent_source_text_assurance import (
    MAX_INDEPENDENT_SOURCE_TEXT_CHARS,
    IndependentSourceTextAssurance,
)


def verify_original_source_claim(
    request: OriginalSourceClaimRequest,
) -> OriginalSourceClaimResponse:
    """Never accept a claim as proof, re-read a selected source, or guess excerpts."""
    binding = claim_request_binding_sha256(request)

    def abstain(reason: str, *, unavailable: bool = False, source: str | None = None):
        return OriginalSourceClaimResponse(
            status="unavailable" if unavailable else "insufficient",
            reason=reason,
            source_ref=source,
            request_binding_sha256=binding,
        )

    claim = _parse_atomic(request.claim_text)
    if claim is None:
        return abstain("claim_grammar_unsupported")

    deps = OrchestrationDependencies.default()
    reader = deps.independent_source_text_assurance._reader
    if not isinstance(reader, AllowlistedHttpsSourceReader):
        return abstain("reader_not_configured", unavailable=True)

    # Checking an exact server-configured URL does not authorize fetching
    # arbitrary user-provided origins (including redirects or private DNS).
    if request.source_uri not in reader._allowed:
        return abstain("source_not_operator_allowed", unavailable=True)

    try:
        observed = reader(request.source_uri)
    except Exception:
        # No source bytes, network errors or secrets in the public response.
        return abstain("source_unavailable", unavailable=True, source=request.source_uri)

    if not isinstance(observed, dict) or observed.get("uri") != request.source_uri:
        return abstain("source_unavailable", unavailable=True, source=request.source_uri)
    body = observed.get("content")
    capture = observed.get("capture_sha256")
    captured_at = observed.get("capture_observed_at")
    quote_hashes = observed.get("observed_quote_unit_sha256")
    if (
        not isinstance(body, str)
        or not 0 < len(body) <= MAX_INDEPENDENT_SOURCE_TEXT_CHARS
        or not isinstance(capture, str) or not re.fullmatch(r"[0-9a-f]{64}", capture)
        or not isinstance(captured_at, str) or not captured_at.endswith("Z")
        or not isinstance(quote_hashes, (tuple, list))
    ):
        return abstain("source_unavailable", unavailable=True, source=request.source_uri)

    candidates: list[str] = []
    for unit in body.split("\n"):
        unit = unit.strip()
        if not 0 < len(unit) <= 500:
            continue
        relation = _relationship(claim, _parse_atomic(unit))
        if relation in {"aligned", "contradicted"}:
            candidates.append(unit)
            # Multiple relevant units must abstain, never cherry-pick a
            # convenient statement or ignore an explicit counterstatement.
            if len(candidates) > 1:
                break
    if len(candidates) != 1:
        return abstain("no_unique_bounded_assertion", source=request.source_uri)

    # Pin all subsequent verification to EXACTLY this same server capture.
    # This adapter is installed internally, never from client JSON. The
    # existing strict assurance still tests source text, unique full unit,
    # original quotation hashes, counterstatements and capture receipt.
    snapshot = {
        "uri": request.source_uri,
        "content": body,
        "capture_sha256": capture,
        "capture_observed_at": captured_at,
        "observed_quote_unit_sha256": list(quote_hashes),
    }

    def same_capture(uri: str):
        if uri != request.source_uri:
            raise ValueError("source identity differs from pinned capture")
        return snapshot

    pinned = replace(
        deps,
        independent_source_text_assurance=IndependentSourceTextAssurance(same_capture),
    )
    state = build_reality_state_from_evidence(
        "Verify a single claim using a server-observed original-source assertion",
        [{"uri": request.source_uri, "content": candidates[0]}],
        freshness_max_age_seconds=request.freshness_max_age_seconds,
        entity=request.entity,
        require_independent_source_text_match=True,
        require_claim_alignment=True,
        claim_text=request.claim_text,
        dependencies=pinned,
    )
    return OriginalSourceClaimResponse(
        status=state["status"],
        reason="bounded_reality_state_evaluated",
        source_ref=request.source_uri,
        request_binding_sha256=binding,
        reality_state=state,
    )


__all__ = ["verify_original_source_claim"]
