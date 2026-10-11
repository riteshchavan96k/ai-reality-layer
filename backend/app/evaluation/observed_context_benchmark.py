"""Step 228: synthetic backend-observed context integrity policy replay.

All publisher bytes below are reviewer-written fixture strings, not real
network captures; live Python.org source-unit acceptance is checked by CI.
"""

from __future__ import annotations

import json
from hashlib import sha256

from backend.app.reality.claim_assertion_alignment import evaluate_claim_alignment
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle

URL = "https://publisher.example.test/source-claim-context"
CLAIM = "Python 3.13.0 was released on October 7, 2024."
CASES = (
    ("exact_single_unit", CLAIM, "aligned"),
    ("whole_line_in_multi_unit_page", "Background text.\n" + CLAIM + "\nFootnote.", "aligned"),
    ("false_prefix_same_paragraph", "It is false that " + CLAIM, "insufficient"),
    ("false_suffix_same_paragraph", "The claim that " + CLAIM + " is false.", "insufficient"),
    ("reported_as_misinformation", "Unverified stories repeat " + CLAIM, "insufficient"),
    ("quoted_inside_other_sentence", 'An example says "' + CLAIM + '"', "insufficient"),
    ("embedded_in_longer_sentence", CLAIM + " But the author refutes it.", "insufficient"),
    ("surrounded_by_other_text", "Other words " + CLAIM + " other words", "insufficient"),
    ("two_standalone_occurrences", CLAIM + "\n" + CLAIM, "insufficient"),
    ("standalone_plus_embedded", CLAIM + "\nIt is false that " + CLAIM, "insufficient"),
    ("no_newline_between_claims", CLAIM + " " + CLAIM, "insufficient"),
    ("line_with_leading_refutation", "This report denies " + CLAIM + "\nLater context.", "insufficient"),
    ("other_structural_units", "Other publication information.\n" + CLAIM, "aligned"),
)


def run() -> dict:
    results = []
    for case_id, observed, expected in CASES:
        bundle = SubmittedEvidenceBundle.from_mappings([{"uri": URL, "content": CLAIM}])
        receipt = IndependentSourceTextAssurance(
            lambda uri: {
                "uri": uri,
                "content": observed,
                "capture_sha256": sha256(observed.encode("utf-8")).hexdigest(),
                "capture_observed_at": "2026-10-11T00:00:00Z",
            }
        ).check(bundle, require_unique_standalone_unit=True)
        decision = evaluate_claim_alignment(CLAIM, bundle, receipt)
        if decision["status"] != expected:
            raise AssertionError("step228_observed_context_oracle_mismatch_" + case_id)
        if decision["semantic_support_verified"] or decision["factual_truth_verified"]:
            raise AssertionError("step228_semantic_truth_overclaim")
        if expected != "aligned" and receipt["status"] != "unverified":
            raise AssertionError("step228_embedded_text_not_refused_" + case_id)
        if expected == "aligned" and receipt["sources"][0].get("assertion_context_status") != "unique_standalone_unit":
            raise AssertionError("step228_legitimate_unit_lost_" + case_id)
        results.append({
            "scenario_id": case_id,
            "expected": expected,
            "actual": decision["status"],
        })
    return {
        "dataset_id": "step228-unique-original-source-unit-adversarial-v1",
        "corpus_type": "synthetic-original-source-unit-fixtures-not-live",
        "scenario_count": len(CASES),
        "legitimate_aligned": sum(item["actual"] == "aligned" for item in results),
        "embedded_incorrectly_aligned": sum(item["expected"] != "aligned" and item["actual"] == "aligned" for item in results),
        "scenarios": results,
        "publisher_authenticated": False,
        "general_semantic_support_verified": False,
        "population_factual_accuracy_established": False,
    }


def main() -> None:
    print(json.dumps(run(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
