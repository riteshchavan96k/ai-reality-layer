# Step 225 — Structural Quote Boundaries for Independently Observed Source Text

## Why this milestone follows Step 224

Step 224 blocked hidden HTML from entering the real HTTPS reader's extracted
text and preserved hard quote boundaries around dropped hidden subtrees.
However the parser still joined *ordinary visible blocks* with spaces.
For example:

```html
<p>Python 3.13.0 was released on</p>
<p>January 1, 1900.</p>
```

Prior extraction made these **different paragraphs** into the single exact
substring "Python 3.13.0 was released on January 1, 1900.", which could satisfy
the strict server-owned independent-source-text assurance despite no single
continuous source unit containing the quotation. Lists and table cells had
the same failure mode. No source needed to be forged at the network level.

## Verified scope of the correction

In `backend/app/reality/allowlisted_https_source_reader.py`,
`_VisibleHtmlText` now inserts explicit newline quote separators at
structural block open/close boundaries (paragraphs, divs, headings, list
items, definitions, table cells/rows, article/section and other block units)
and visible `<br>`/`<hr>` boundaries. Newlines are preserved as **exact
source text boundaries** so a full submitted excerpt cannot silently match
across them. Nested, consecutive or empty block tags do not create fake
continuous text segments. Text inside formatting-only inline elements
`<strong>`, `<span>`, `<em>` still forms a contiguous excerpt.

Step 224's excluded-subtree/newline boundary, hiding attributes, parser
nesting maximum and bounded gzip decoding remain intact. We do **not**
strip newline separators in the strict matcher; it continues to compare the
complete submitted excerpt as a literal substring in the backend-observed
source extraction. We do **not** normalize or relax the matched quote.
Cross-paragraph submissions may now be rejected, **intentionally and
conservatively**. This is a documented behavior change for improved evidence
integrity, not backward-compatible free-text flattening.

No alteration to network operator allowlists, DNS/IP validation, TLS hostname
verification, redirect refusal, response byte ceilings, historical
capture SHA/time audits or Step 223 authoritative capture freshness.

## Tests and independent evaluation

- `backend/tests/test_step225.py`: parameterized adversarial structural quote
  examples (paragraphs, divs, heading + paragraph, lists, table cells and
  rows, line breaks), valid inline controls, existing Step 224 hidden text
  behavior, plain-text response parity, and full strict Reality State
  behavior with injected **fake** HTTPS connection.
- `backend/app/evaluation/structural_quote_benchmark.py`: 16 labeled,
  deliberately **synthetic** cases (12 cross-block false-quote constructions
  that must be rejected; 4 legitimate whole-unit quotations that must remain
  present). No publisher dataset, blind annotation, statistically meaningful
  error bounds, semantic entailment or factual truth is claimed.
- `.github/workflows/backend-tests.yml`: the Step 225 replay executes
  after the same regression suite and unchanged Step 217/218/220/223/224
  replays.
- The independent `.github/workflows/step222-live-source-smoke.yml`
  continues to execute genuine operator-approved DNS/IP-pinned HTTPS/TLS
  transactions and require positive and negative strict FastAPI outcomes.
  Do not treat fake-transport regression tests as live observations.

## Reproduction and acceptance

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
python -m backend.app.evaluation.capture_freshness_benchmark
python -m backend.app.evaluation.html_visibility_quality_benchmark
python -m backend.app.evaluation.structural_quote_benchmark
```

Before marking complete: all historical replays and full Python 3.13 suite
must pass on the final feature head; the real Step 222 live publisher canary
must pass at the same SHA; feature PR must merge; both must pass on merged
main; final status synchronization must merge and both must pass on exact
current main SHA.

## What is still *not* demonstrated

This is conservative *source text structure*, not a browser. HTML5 error
correction, CSS generated content, JavaScript/shadow DOM, external styles,
visual rendering, provider authentication, published truthfulness, semantic
support or historical publication time are not solved. A quotation may still
be misleading through context; matching exact text cannot establish that
the statement is true. A single live HTTPS publisher smoke test cannot
measure generalization or production readiness.

## Verified hosted evidence

Step 225 was implemented through [PR #226](https://github.com/riteshchavan96k/ai-reality-layer/pull/226).

- Final feature head `a74bd488539ade2abf2df98d48ae8cac67b80718`: [backend CI 38084927193](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38084927193) successful (**2,289 tests passed**, compilation and all Steps 217/218/220/223/224/225 replays); [real publisher HTTPS CI 38084927096](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38084927096) successful.
- Independently merged `main` SHA `3f1846577312d30d990a4d174d4a267ce78cdad5`: [backend CI 38084991634](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38084991634) successful (**2,289 tests**) and [genuine HTTPS CI 38084991610](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38084991610) successful.
- Synthetic Step 225 structural replay: **16/16 expected outcomes**, comprising 12 forged cross-block examples rejected and 4 legitimate inline excerpts preserved. These are policy fixture results, not population-level publisher performance or factual truth.
- The final status-documentation synchronization commit must independently pass both hosted workflows on its exact resulting current `main` SHA before Step 225 is declared complete.

There is no claim that preserving DOM structural boundaries establishes semantic entailment, original-source authorship, general browser rendering, or production reliability.
