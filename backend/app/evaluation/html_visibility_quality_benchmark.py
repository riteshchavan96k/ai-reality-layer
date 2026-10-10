"""Step 224: synthetic hidden-HTML exact-quote visibility evaluation.

Fixtures are deliberately constructed for parser policy assurance, NOT real
publisher HTML or factual/semantic correctness. No network is used here.
"""

from __future__ import annotations

import json
from typing import Any

from backend.app.reality.allowlisted_https_source_reader import (
    _decode_observed_content,
)

TRUE = "Python 3.13.0 was released on October 7, 2024."
FORGED = "Python 3.13.0 was released on January 1, 1900."

CASES = (
    ("hidden-boolean", "<div hidden>" + FORGED + "</div>", False),
    ("aria-hidden", "<div aria-hidden='true'>" + FORGED + "</div>", False),
    ("css-display-none", "<p style='display:none'>" + FORGED + "</p>", False),
    ("css-visibility-hidden", "<p style='visibility:hidden'>" + FORGED + "</p>", False),
    ("css-content-visibility-hidden", "<p style='content-visibility:hidden'>" + FORGED + "</p>", False),
    ("inert", "<div inert>" + FORGED + "</div>", False),
    ("template", "<template>" + FORGED + "</template>", False),
    ("iframe-fallback", "<iframe>" + FORGED + "</iframe>", False),
    ("closed-details", "<details><summary>More</summary>" + FORGED + "</details>", False),
    ("hidden-removal-word-stitch", "<p>Python 3.13.0 was released on <span hidden>NOT</span>January 1, 1900.</p>", False),
    ("visible-inline", "<p>" + TRUE.replace("October", "<b>October</b>") + "</p>", True),
)


def run_benchmark() -> dict[str, Any]:
    cases = []
    hidden_present = 0
    expected_visible_preserved = 0
    for name, fragment, should_match in CASES:
        html = "<html><head><title>ignored</title></head><body>" + fragment
        html += "<p>Python 3.13.0 release index.</p></body></html>"
        observed = _decode_observed_content(html.encode(), "text/html; charset=utf-8")
        excerpt = TRUE if should_match else FORGED
        matched = excerpt in observed
        if matched != should_match:
            raise AssertionError("HTML visibility fixture violated: " + name)
        if not should_match and matched:
            hidden_present += 1
        if should_match and matched:
            expected_visible_preserved += 1
        cases.append({
            "id": name,
            "should_text_be_exposed": should_match,
            "actually_exposed": matched,
        })
    return {
        "dataset_id": "step224-synthetic-html-visibility-v1",
        "corpus_type": "handwritten-synthetic-html-no-original-publisher-captures",
        "case_count": len(CASES),
        "hidden_cases": sum(not c[2] for c in CASES),
        "hidden_false_exposure_count": hidden_present,
        "genuine_visible_quote_preserved_count": expected_visible_preserved,
        "correct_expected_outcomes": len(cases),
        "cases": cases,
        "limitations": [
            "This is HTMLParser-based conservative extraction, not a browser rendering engine.",
            "No external CSS, JavaScript, layout, font, accessibility or visual tree is executed.",
            "Synthetic cases are not generalizable original-source field false-positive rates.",
            "Text presence is not publisher endorsement, factual truth or semantic entailment.",
            "Live network test remains separate in the Step 222 HTTPS publisher workflow.",
        ],
    }


def main() -> int:
    print(json.dumps(run_benchmark(), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
