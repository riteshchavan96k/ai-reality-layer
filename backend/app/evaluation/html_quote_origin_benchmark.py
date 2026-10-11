"""Step 230: deterministic HTML quote-scope policy benchmark.

Synthetic hand-authored HTML; NOT a live publisher factual accuracy dataset.
The separate fixed original-publisher HTTPS canary remains mandatory.
"""

from __future__ import annotations

import json
from hashlib import sha256

from backend.app.reality.allowlisted_https_source_reader import _VisibleHtmlText
from backend.app.reality.claim_assertion_alignment import evaluate_claim_alignment
from backend.app.reality.independent_source_text_assurance import IndependentSourceTextAssurance
from backend.app.reality.submitted_evidence import SubmittedEvidenceBundle


URI = "https://publisher.example.test/quoted-assertion"
CLAIM = "Python 3.13.0 is a stable release."
CASES = (
    ("direct_paragraph", "<p>" + CLAIM + "</p>", "aligned"),
    ("direct_heading", "<h2>" + CLAIM + "</h2>", "aligned"),
    ("direct_with_unrelated_quote", "<p>" + CLAIM + "</p><blockquote>Unrelated historic remark.</blockquote>", "aligned"),
    ("quoted_block", "<blockquote>" + CLAIM + "</blockquote>", "insufficient"),
    ("quoted_paragraph", "<blockquote><p>" + CLAIM + "</p></blockquote>", "insufficient"),
    ("quoted_inline_element", "<p><q>" + CLAIM + "</q></p>", "insufficient"),
    ("quoted_emphasis", "<blockquote><strong>" + CLAIM + "</strong></blockquote>", "insufficient"),
    ("quoted_list", "<blockquote><ul><li>" + CLAIM + "</li></ul></blockquote>", "insufficient"),
    ("duplicate_quoted_and_plain", "<h2>" + CLAIM + "</h2><blockquote>" + CLAIM + "</blockquote>", "insufficient"),
    ("quoted_with_another_context", "<div><p>Introduction.</p><blockquote>" + CLAIM + "</blockquote></div>", "insufficient"),
)


def run() -> dict:
    records = []
    for label, markup, expected in CASES:
        parser = _VisibleHtmlText()
        parser.feed("<html><body>" + markup + "</body></html>")
        observed = parser.text()
        quote_digests = list(parser.quote_unit_digests())
        bundle = SubmittedEvidenceBundle.from_mappings([
            {"uri": URI, "content": CLAIM}
        ])
        receipt = IndependentSourceTextAssurance(
            lambda uri: {
                "uri": uri,
                "content": observed,
                "capture_sha256": sha256(observed.encode()).hexdigest(),
                "capture_observed_at": "2026-10-11T00:00:00Z",
                "observed_quote_unit_sha256": quote_digests,
            }
        ).check(bundle, require_unique_standalone_unit=True)
        decision = evaluate_claim_alignment(CLAIM, bundle, receipt)
        if decision["status"] != expected:
            raise AssertionError("step230_html_quote_policy_mismatch_" + label)
        if decision["semantic_support_verified"] or decision["factual_truth_verified"]:
            raise AssertionError("step230_false_factual_truth_claim")
        records.append({
            "scenario_id": label, "expected": expected,
            "actual": decision["status"],
        })
    return {
        "dataset_id": "step230-handwritten-html-quote-origin-v1",
        "corpus_type": "synthetic-html-not-live-publisher",
        "scenario_count": len(CASES),
        "unquoted_aligned": sum(x["expected"] == "aligned" and x["actual"] == "aligned" for x in records),
        "quote_related_incorrectly_aligned": sum(x["expected"] != "aligned" and x["actual"] == "aligned" for x in records),
        "scenarios": records,
        "semantic_support_verified": False,
        "factual_truth_verified": False,
        "population_accuracy_established": False,
    }


def main():
    print(json.dumps(run(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
