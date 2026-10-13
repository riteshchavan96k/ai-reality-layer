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
    OriginalSourceEvidence,
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



def _verified_source_evidence(
    state: dict,
    *,
    selected_unit: str,
    source_uri: str,
    source_capture_sha256: str,
    source_capture_observed_at: str,
) -> OriginalSourceEvidence | None:
    """Only emit text when the *same capture* passed every existing source gate.

    Never echo a candidate if an assurance/quote/counterstatement check has
    refused it. This field is evidence of observed text, not factual truth.
    """
    if not isinstance(state, dict) or state.get("status") not in {"supported", "uncertain"}:
        return None
    evidence = state.get("evidence")
    if not isinstance(evidence, dict):
        return None
    assurance = evidence.get("independent_source_text_assurance")
    alignment = evidence.get("claim_alignment")
    if not isinstance(assurance, dict) or not isinstance(alignment, dict):
        return None
    freshness = state.get("freshness")
    conflicts = state.get("conflicts")
    verification = state.get("verification")
    confidence = state.get("confidence_signals")
    if (
        not isinstance(freshness, dict)
        or freshness.get("status") != "usable"
        or freshness.get("stale_count") != 0
        or freshness.get("unknown_count") != 0
        or not isinstance(conflicts, dict)
        or conflicts.get("conflict_count") != 0
        or not isinstance(verification, dict)
        or verification.get("status") != "completed"
        or not isinstance(confidence, dict)
        or confidence.get("status") != state["status"]
    ):
        return None
    rows = assurance.get("sources")
    decisions = alignment.get("source_decisions")
    if (
        assurance.get("status") != "exact_text_observed"
        or assurance.get("source_count") != 1
        or assurance.get("matched_source_count") != 1
        or assurance.get("publisher_authenticated") is not False
        or assurance.get("semantic_support_verified") is not False
        or alignment.get("method") != "bounded_atomic_assertion_comparison"
        or alignment.get("status") not in {"aligned", "contradicted"}
        or alignment.get("semantic_support_verified") is not False
        or alignment.get("factual_truth_verified") is not False
        or not isinstance(rows, list) or len(rows) != 1
        or not isinstance(decisions, list) or len(decisions) != 1
    ):
        return None
    source_row, decision_row = rows[0], decisions[0]
    if not isinstance(source_row, dict) or not isinstance(decision_row, dict):
        return None
    if (
        source_row.get("source_ref") != source_uri
        or source_row.get("status") != "exact_text_observed"
        or source_row.get("assertion_context_status") != "unique_standalone_unit"
        or source_row.get("source_counterstatement_status")
        != "no_bounded_counterstatement_observed"
        or source_row.get("source_quote_context_status") != "no_matching_html_quote_unit"
        or source_row.get("reason") is not None
        or source_row.get("capture_sha256") != source_capture_sha256
        or source_row.get("capture_observed_at") != source_capture_observed_at
        or decision_row.get("source_ref") != source_uri
        or decision_row.get("relationship") != (
            "aligned" if alignment["status"] == "aligned" else "contradicted"
        )
        or (alignment["status"] == "aligned" and state["status"] != "supported")
        or not isinstance(selected_unit, str)
        or not 0 < len(selected_unit) <= 500
    ):
        return None
    return OriginalSourceEvidence(
        text=selected_unit,
        text_sha256=sha256(selected_unit.encode("utf-8")).hexdigest(),
        source_capture_sha256=source_capture_sha256,
        source_capture_observed_at=source_capture_observed_at,
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
        source_evidence=_verified_source_evidence(
            state,
            selected_unit=candidates[0],
            source_uri=request.source_uri,
            source_capture_sha256=capture,
            source_capture_observed_at=captured_at,
        ),
    )


__all__ = ["verify_original_source_claim"]
