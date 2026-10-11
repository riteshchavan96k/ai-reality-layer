"""Step 229 original-source cross-unit counterstatement policy replay.

Reviewer-authored source text and observer transports are synthetic. This
tests one bounded policy, not statistical truth or language understanding.
"""

from __future__ import annotations

from hashlib import sha256
import json

from backend.app.reality.claim_assertion_alignment import evaluate_claim_alignment
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle

URI = "https://publisher.example.test/source-wide-context"
CLAIM = "Python 3.13.0 was released on October 7, 2024."
OTHER_DATE = "Python 3.13.0 was released on January 1, 1900."
NEGATED = "Python 3.13.0 was not released on October 7, 2024."
STABLE = "This is the stable release of Python 3.13.0"
STABLE_NEGATED = "Python 3.13.0 is not a stable release."

# Case_id, excerpt, proposition, whole separately observed publisher text,
# oracle decision. Every case has a unique complete excerpt.
CASES = (
    ("single_valid", CLAIM, CLAIM, CLAIM, "aligned"),
    ("unrelated_second_unit", CLAIM, CLAIM, CLAIM + "\nAnother fact.", "aligned"),
    ("different_entity", CLAIM, CLAIM, CLAIM + "\nPython 3.12.0 was not released on October 7, 2024.", "aligned"),
    ("heading_unchallenged", STABLE, "Python 3.13.0 is a stable release.", STABLE, "aligned"),
    ("explicit_negation_next_unit", CLAIM, CLAIM, CLAIM + "\n" + NEGATED, "insufficient"),
    ("negation_before_claim", CLAIM, CLAIM, NEGATED + "\n" + CLAIM, "insufficient"),
    ("different_single_release_date", CLAIM, CLAIM, CLAIM + "\n" + OTHER_DATE, "insufficient"),
    ("date_discrepancy_before_claim", CLAIM, CLAIM, OTHER_DATE + "\n" + CLAIM, "insufficient"),
    ("untrue_that_claim", CLAIM, CLAIM, CLAIM + "\nIt is untrue that " + CLAIM, "insufficient"),
    ("false_that_claim", CLAIM, CLAIM, CLAIM + "\nIt is false that " + CLAIM, "insufficient"),
    ("stable_publisher_opposite", STABLE, "Python 3.13.0 is a stable release.", STABLE + "\n" + STABLE_NEGATED, "insufficient"),
    ("stable_opposite_before_heading", STABLE, "Python 3.13.0 is a stable release.", STABLE_NEGATED + "\n" + STABLE, "insufficient"),
    ("irrelevant_other_release", CLAIM, CLAIM, CLAIM + "\nPython 3.12.0 was released on January 1, 1900.", "aligned"),
    ("distinct_description", CLAIM, CLAIM, CLAIM + "\nPython 3.13.0 is a stable release.", "aligned"),
)


def run() -> dict:
    decisions = []
    for case_id, excerpt, claim, observed, expected in CASES:
        bundle = SubmittedEvidenceBundle.from_mappings([{"uri": URI, "content": excerpt}])
        assurance = IndependentSourceTextAssurance(
            lambda uri: {
                "uri": uri,
                "content": observed,
                "capture_sha256": sha256(observed.encode()).hexdigest(),
                "capture_observed_at": "2026-10-11T00:00:00Z",
                "observed_quote_unit_sha256": [],
            }
        ).check(bundle, require_unique_standalone_unit=True)
        actual = evaluate_claim_alignment(claim, bundle, assurance)
        if actual["status"] != expected:
            raise AssertionError("step229_wrong_context_decision_" + case_id)
        if expected == "insufficient":
            reason = assurance["sources"][0]["reason"]
            expected_reason = (
                "excerpt_not_unique_standalone_source_unit"
                if case_id in {"untrue_that_claim", "false_that_claim"}
                else "independent_source_explicit_counterstatement"
            )
            if reason != expected_reason:
                raise AssertionError("step229_wrong_guard_precedence_" + case_id)
        if actual["semantic_support_verified"] or actual["factual_truth_verified"]:
            raise AssertionError("step229_false_semantic_truth_assurance")
        decisions.append({"scenario_id": case_id, "expected": expected, "actual": actual["status"]})
    return {
        "dataset_id": "step229-independent-source-counterstatement-synthetic-v1",
        "corpus_type": "reviewer-written-independent-reader-fixtures-not-live-publisher",
        "scenario_count": len(CASES),
        "legitimate_aligned": sum(x["actual"] == "aligned" for x in decisions),
        "counterstatement_incorrectly_aligned": sum(
            x["expected"] == "insufficient" and x["actual"] == "aligned"
            for x in decisions
        ),
        "step228_duplicate_denials_rejected": 2,
        "step229_explicit_counterstatements_rejected": 6,
        "scenarios": decisions,
        "semantic_support_verified": False,
        "factual_truth_verified": False,
        "population_accuracy_established": False,
    }


def main() -> None:
    print(json.dumps(run(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
