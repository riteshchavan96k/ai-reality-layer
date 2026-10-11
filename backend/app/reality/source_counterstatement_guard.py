"""Step 229: bounded opposite assertions across one independently observed source.

A positive result says only that NO recognized *explicit* opposite unit was
found in the observed text. This is NOT proof of semantic consistency or truth.
No caller document, URL, extra network fetch, model, or third-party assessment
is consulted; the upstream independent reader owns the observed text.
"""

from __future__ import annotations

from backend.app.reality.claim_assertion_alignment import (
    _parse_atomic,
    _relationship,
)

MAX_OBSERVED_SOURCE_CHARS = 200_000

def has_bounded_source_counterstatement(
    observed_text: str, source_excerpt: str
) -> bool:
    """True only when another observed full text unit explicitly rejects it.

    Evaluation is linear in the already bounded captured text and never
    manufactures a fragment by stitching HTML boundaries or other lines.
    The expected excerpt must be a complete unit (Step 228 separately
    verifies uniqueness). No semantic authority is assigned to the result.
    """
    if (
        not isinstance(observed_text, str)
        or not isinstance(source_excerpt, str)
        or len(observed_text) > MAX_OBSERVED_SOURCE_CHARS
    ):
        raise ValueError("bounded source counterstatement input invalid")

    source_assertion = _parse_atomic(source_excerpt)
    if source_assertion is None:
        return False  # Outside grammar: Step 227 already cannot align it.

    for unit in observed_text.split("\n"):
        unit = unit.strip()
        if not unit or unit == source_excerpt.strip():
            continue

        other = _parse_atomic(unit)
        if _relationship(source_assertion, other) == "contradicted":
            return True

    return False


__all__ = [
    "MAX_OBSERVED_SOURCE_CHARS",
    "has_bounded_source_counterstatement",
]
