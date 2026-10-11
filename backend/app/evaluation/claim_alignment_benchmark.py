"""Step 227 fixed synthetic claim-alignment policy replay.

These reviewer-authored cases are NOT blinded human factual annotation,
population precision estimates, or proof of semantic entailment.
"""

from __future__ import annotations

import json
from hashlib import sha256

from backend.app.reality.claim_assertion_alignment import evaluate_claim_alignment
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


URI = "https://publisher.example.test/atomic-assertion"
CLAIM = "Python 3.13.0 was released on October 7, 2024."
CASES = (
    ("direct_statement", CLAIM, "aligned"),
    ("different_date", "Python 3.13.0 was released on January 1, 1900.", "contradicted"),
    ("direct_negation", "Python 3.13.0 was not released on October 7, 2024.", "contradicted"),
    ("different_entity", "Python 3.12.0 was released on October 7, 2024.", "insufficient"),
    ("wrong_predicate", "Python 3.13.0 is generally available.", "insufficient"),
    ("reported_disinformation", "The claim that Python 3.13.0 was released on October 7, 2024 is false.", "insufficient"),
    ("quoted_without_attribution", '"Python 3.13.0 was released on October 7, 2024."', "insufficient"),
    ("hedged_claim", "Python 3.13.0 might be released on October 7, 2024.", "insufficient"),
    ("multiple_sentences", CLAIM + " But another source disputes it.", "insufficient"),
    ("line_break", CLAIM + "\nOther sentence.", "insufficient"),
    ("unrelated_date_claim", "Python 3.12.0 was released on October 2, 2023.", "insufficient"),
    ("unsupported_modality", "Python 3.13.0 could be released on October 7, 2024.", "insufficient"),
    ("unrelated_description", "Python 3.13.0 is a programming language.", "insufficient"),
    ("missing_finite_verb", "Release date October 7, 2024.", "insufficient"),
    ("unquoted_negative", "Python 3.13.0 was not released on January 1, 1900.", "insufficient"),
    ("no_complete_sentence", "Python 3.13.0 was released on October 7, 2024", "insufficient"),
)


def run() -> dict:
    results = []
    for case_id, observed, expected in CASES:
        bundle = SubmittedEvidenceBundle.from_mappings([{
            "uri": URI, "content": observed,
        }])
        receipt = {
            "status": "exact_text_observed",
            "sources": [{
                "source_ref": URI,
                "status": "exact_text_observed",
                "capture_sha256": sha256(observed.encode()).hexdigest(),
                "capture_observed_at": "2026-10-11T00:00:00Z",
            }],
        }
        actual = evaluate_claim_alignment(CLAIM, bundle, receipt)
        if actual["status"] != expected:
            raise AssertionError(f"claim_alignment_policy_mismatch_{case_id}")
        if actual["semantic_support_verified"] or actual["factual_truth_verified"]:
            raise AssertionError("claim_alignment_overclaimed_truth")
        results.append({"scenario_id": case_id, "expected": expected, "actual": actual["status"]})
    return {
        "dataset_id": "step227-handwritten-atomic-assertion-policy-v1",
        "corpus_type": "synthetic-reviewed-text-not-live-publisher",
        "scenario_count": len(CASES),
        "legitimate_aligned": sum(x["expected"] == "aligned" for x in results),
        "nonaligned_incorrectly_supported": sum(
            x["expected"] != "aligned" and x["actual"] == "aligned" for x in results
        ),
        "scenarios": results,
        "semantic_support_verified": False,
        "population_factual_accuracy_established": False,
    }


def main() -> None:
    print(json.dumps(run(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
