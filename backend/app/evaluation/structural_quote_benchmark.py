"""Step 225: synthetic HTML structural quote-contiguity benchmark.

This deterministic fixture measures a reader's structural boundary behavior,
not visual browser rendering, real-world support or factual accuracy.
"""

from __future__ import annotations

import json
from typing import Any
from backend.app.reality.allowlisted_https_source_reader import _decode_observed_content

PREFIX = "Python 3.13.0 was released on"
FALSE_END = "January 1, 1900."
TRUE_QUOTE = "Python 3.13.0 was released on October 7, 2024."
FORGED = PREFIX + " " + FALSE_END

SEPARATED = (
    ("adjacent-paragraphs", "<p>" + PREFIX + "</p><p>" + FALSE_END + "</p>"),
    ("adjacent-divs", "<div>" + PREFIX + "</div><div>" + FALSE_END + "</div>"),
    ("heading-paragraph", "<h2>" + PREFIX + "</h2><p>" + FALSE_END + "</p>"),
    ("list-items", "<ul><li>" + PREFIX + "</li><li>" + FALSE_END + "</li></ul>"),
    ("table-cells", "<table><tr><td>" + PREFIX + "</td><td>" + FALSE_END + "</td></tr></table>"),
    ("table-rows", "<table><tr><td>" + PREFIX + "</td></tr><tr><td>" + FALSE_END + "</td></tr></table>"),
    ("br-line-break", "<p>" + PREFIX + "<br>" + FALSE_END + "</p>"),
    ("hr-line-break", "<p>" + PREFIX + "<hr>" + FALSE_END + "</p>"),
    ("nested-blocks", "<section><p>" + PREFIX + "</p><p>" + FALSE_END + "</p></section>"),
    ("block-to-text", "<p>" + PREFIX + "</p>" + FALSE_END),
    ("blockquote-to-paragraph", "<blockquote>" + PREFIX + "</blockquote><p>" + FALSE_END + "</p>"),
    ("header-to-main", "<header>" + PREFIX + "</header><main>" + FALSE_END + "</main>"),
)
CONTIGUOUS = (
    ("inline-strong", "<p>" + PREFIX + " <strong>October 7, 2024.</strong></p>"),
    ("inline-span", "<div>" + PREFIX + " <span>October 7, 2024.</span></div>"),
    ("single-paragraph", "<p>" + TRUE_QUOTE + "</p>"),
    ("single-table-cell", "<td>" + TRUE_QUOTE + "</td>"),
)


def run_benchmark() -> dict[str, Any]:
    samples = []
    for key, markup in SEPARATED:
        output = _decode_observed_content(markup.encode(), "text/html")
        if FORGED in output or "\n" not in output:
            raise AssertionError("structural quote spoof acceptance: " + key)
        samples.append({"fixture": key, "expected": "rejected", "actual": "rejected"})
    for key, markup in CONTIGUOUS:
        output = _decode_observed_content(markup.encode(), "text/html")
        if TRUE_QUOTE not in output:
            raise AssertionError("valid inline quote lost: " + key)
        samples.append({"fixture": key, "expected": "preserved", "actual": "preserved"})
    return {
        "dataset_id": "step225-structural-quote-contiguity-synthetic-v1",
        "corpus_type": "synthetic-html-fixtures-not-live-publisher-corpus",
        "scenario_count": len(samples),
        "cross_block_false_acceptances": 0,
        "cross_block_cases": len(SEPARATED),
        "legitimate_quote_preserved": len(CONTIGUOUS),
        "correct_expected_outcomes": len(samples),
        "cases": samples,
        "publisher_authenticated": False,
        "semantic_support_verified": False,
        "limitations": [
            "A declared HTML structural-block test, not full browser rendering.",
            "Exact text observation does not establish meaning, authorship or factual truth.",
            "Cross-paragraph excerpts now conservatively abstain rather than reconstruct source quotes.",
            "Synthetic error rates cannot estimate population-level publisher behavior.",
            "Actual public HTTPS publisher canary is independently gated in Step 222 workflow.",
        ],
    }


def main() -> int:
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
