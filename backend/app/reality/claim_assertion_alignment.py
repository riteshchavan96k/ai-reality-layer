"""Step 227: conservative atomic claim-to-observed-excerpt comparison.

This is *not* general language inference, publisher authentication, a
cryptographic signature, or a factual-truth check. A positive result describes
only a narrowly parsed, exact atomic assertion in independently observed
source text. Any ambiguity or missing capture metadata abstains.
"""

from __future__ import annotations

import re
from typing import Any

from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle

MAX_ATOMIC_CLAIM_CHARS = 500

# Refuse reported/conditional/quoted language rather than trying to interpret
# it as an assertion from the source. This is a defensive heuristic, not a
# complete HTML or linguistic context detector.
_UNSAFE_WORDS = re.compile(
    r"\b(?:claim|claims|claimed|alleged|allegedly|rumor|rumour|"
    r"reported|reports|reportedly|supposed|supposedly|false|"
    r"according|perhaps|maybe|might|could|would|if|unless|"
    r"although|however|but|never|without|denies|denied)\b",
    re.IGNORECASE,
)
_RELEASE = re.compile(
    r"(?P<subject>[A-Za-z][A-Za-z0-9_. -]{0,100}?)"
    r" was (?P<neg>not )?released on "
    r"(?P<value>[A-Za-z0-9, -]{3,80})\.",
    re.IGNORECASE,
)
_PROPERTY = re.compile(
    r"(?P<subject>[A-Za-z][A-Za-z0-9_. -]{0,100}?)"
    r" (?P<verb>is|was) (?P<neg>not )?"
    r"(?P<value>[A-Za-z][A-Za-z0-9_. -]{0,90})\.",
    re.IGNORECASE,
)
_STABLE_RELEASE_DECLARATION = re.compile(
    r"This is the stable release of (?P<subject>[A-Za-z][A-Za-z0-9_. -]{0,100})",
    re.IGNORECASE,
)
_DISALLOWED_QUOTES = frozenset("'\"\u2018\u2019\u201c\u201d\u00ab\u00bb\u0060")


def _norm(value: str) -> str:
    return " ".join(value.split()).casefold()


def _parse_atomic(text: str) -> tuple[str, str, str, bool] | None:
    if (
        not isinstance(text, str)
        or not (0 < len(text) <= MAX_ATOMIC_CLAIM_CHARS)
        or "\n" in text
        or "\r" in text
        or any(char in text for char in _DISALLOWED_QUOTES)
        or _UNSAFE_WORDS.search(text)
    ):
        return None
    clean = " ".join(text.strip().split())
    original_release = _STABLE_RELEASE_DECLARATION.fullmatch(clean)
    if original_release:
        subject = _norm(original_release.group("subject"))
        if not re.search(r"\b(?:not|no|is|was|said|says|states|that)\b", subject):
            return subject, "is", "a stable release", False
        return None
    match = _RELEASE.fullmatch(clean)
    method = "release_date" if match else "copular_property"
    if match is None:
        match = _PROPERTY.fullmatch(clean)
    if match is None:
        return None
    subject = _norm(match.group("subject"))
    value = _norm(match.group("value"))
    # Ambiguous negation or references embedded in an alleged subject/value
    # are not safe to treat as positive atomic propositions.
    if (
        not subject or not value
        or re.search(r"\b(?:not|no|is|was|said|says|states|that)\b", subject)
        or re.search(r"\b(?:not|no|is|was|said|says|states|that)\b", value)
    ):
        return None
    predicate = "released_on" if method == "release_date" else match.group("verb").lower()
    return subject, predicate, value, bool(match.group("neg"))


def _relationship(claim: tuple[str, str, str, bool] | None,
                  observed: tuple[str, str, str, bool] | None) -> str:
    if claim is None or observed is None:
        return "insufficient"
    cs, cp, cv, cn = claim
    os, op, ov, on = observed
    if cs != os or cp != op:
        return "insufficient"
    if cv == ov:
        return "aligned" if cn == on else "contradicted"
    # An explicit release date is single-valued only when both assertions
    # are positive; unlike adjectives, different positive dates conflict.
    if cp == "released_on" and not cn and not on:
        return "contradicted"
    return "insufficient"


def evaluate_claim_alignment(
    claim_text: str,
    bundle: SubmittedEvidenceBundle,
    source_assurance: dict[str, Any],
) -> dict[str, Any]:
    """Require all source-scoped, independently captured excerpts to align.

    The caller does not get to submit an authoritative semantic judgement.
    A source-attestation mismatch, absent digest/time, or an unrecognized
    grammatical form cannot produce an aligned result.
    """
    if not isinstance(claim_text, str) or not claim_text.strip():
        raise ValueError("claim_text must be a non-empty string")
    if len(claim_text) > MAX_ATOMIC_CLAIM_CHARS:
        raise ValueError("claim_text is too long")
    if not isinstance(bundle, SubmittedEvidenceBundle):
        raise ValueError("bundle must be a SubmittedEvidenceBundle")
    if not isinstance(source_assurance, dict):
        raise ValueError("source_assurance must be a dictionary")
    parsed = _parse_atomic(claim_text)
    rows = source_assurance.get("sources")
    by_uri = {}
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("source_ref"), str):
                if row["source_ref"] in by_uri:
                    by_uri = {}
                    break
                by_uri[row["source_ref"]] = row

    items = []
    reasons = []
    for document in bundle.documents:
        attestation = by_uri.get(document.uri, {})
        eligible = (
            source_assurance.get("status") == "exact_text_observed"
            and attestation.get("status") == "exact_text_observed"
            and attestation.get("assertion_context_status") == "unique_standalone_unit"
            and attestation.get("source_counterstatement_status") == "no_bounded_counterstatement_observed"
            and attestation.get("source_quote_context_status") == "no_matching_html_quote_unit"
            and isinstance(attestation.get("capture_sha256"), str)
            and bool(re.fullmatch(r"[0-9a-f]{64}", attestation["capture_sha256"]))
            and isinstance(attestation.get("capture_observed_at"), str)
            and attestation["capture_observed_at"].endswith("Z")
        )
        if not eligible:
            relationship = "insufficient"
            # Never echo arbitrary reader errors, source text or credentials.
            # All possible reason codes below are fixed, trusted enum values.
            if (
                attestation.get("reason") == "original_source_quoted_html_unit"
                or attestation.get("source_quote_context_status") == "quoted_source_unit"
            ):
                code = "source_quoted_unit"
            elif attestation.get("reason") == "independent_source_explicit_counterstatement":
                code = "source_counterstatement_observed"
            elif (
                attestation.get("status") != "exact_text_observed"
                or source_assurance.get("status") != "exact_text_observed"
            ):
                code = "independent_source_unverified"
            elif (
                attestation.get("assertion_context_status") != "unique_standalone_unit"
                or attestation.get("source_counterstatement_status") != "no_bounded_counterstatement_observed"
                or attestation.get("source_quote_context_status") != "no_matching_html_quote_unit"
            ):
                code = "source_assertion_context_unverified"
            else:
                code = "source_capture_receipt_invalid"
        elif parsed is None:
            relationship = "insufficient"
            code = "claim_grammar_unsupported"
        else:
            source_parsed = _parse_atomic(document.content)
            if source_parsed is None:
                relationship = "insufficient"
                code = "source_grammar_unsupported"
            else:
                relationship = _relationship(parsed, source_parsed)
                code = {
                    "aligned": "bounded_assertion_aligned",
                    "contradicted": "bounded_assertion_contradicted",
                    "insufficient": "atomic_relationship_undetermined",
                }[relationship]
        items.append({"source_ref": document.uri, "relationship": relationship})
        reasons.append({"source_ref": document.uri, "code": code})
    outcomes = [x["relationship"] for x in items]
    if outcomes and all(x == "aligned" for x in outcomes):
        status = "aligned"
    elif outcomes and all(x == "contradicted" for x in outcomes):
        status = "contradicted"
    elif "aligned" in outcomes and "contradicted" in outcomes:
        status = "conflicting"
    else:
        status = "insufficient"
    return {
        "status": status,
        "method": "bounded_atomic_assertion_comparison",
        "source_count": len(items),
        "source_decisions": items,
        "decision_reasons": reasons,
        "semantic_support_verified": False,
        "factual_truth_verified": False,
    }


__all__ = ["MAX_ATOMIC_CLAIM_CHARS", "evaluate_claim_alignment"]
