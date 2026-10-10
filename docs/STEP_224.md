# Step 224 — Conservative HTML Visibility Filtering for Exact Source Evidence

## Verified gap after Step 223

Steps 221–223 provided a restricted live HTTPS reader, independently observed
capture metadata, and server-authoritative observation freshness. But the
reader's HTML parser only dropped `script`, `style`, `head`, `noscript`
and `svg` containers. Other common non-rendered HTML subtrees were
accidentally considered readable source evidence.

An adversarial or badly configured publisher page could put a forged claim
inside `<template>`, `<div hidden>`, `aria-hidden=true`, or a simple
inline `display:none` element. The strict source text gate could then find
the forged excerpt in the parser output even though the element is normally
hidden from a reader. This is a **text-extraction provenance gap**, not a
problem solvable by adding a higher confidence score.

## Scoped implementation

`backend/app/reality/allowlisted_https_source_reader.py` now conservatively
excludes descendants inside common non-readable HTML elements:

- `script`, `style`, `head`, `noscript`, `svg`, `template`,
  `iframe`, `object`, `canvas`.
- Any node carrying the HTML `hidden` or `inert` attribute; nodes with
  `aria-hidden=true` (case-/whitespace-insensitive).
- Simple inline `display:none`, `visibility:hidden`,
  `visibility:collapse`, `content-visibility:hidden`, including case
  variations, CSS comments and trailing `!important`.
- Closed `<details>` descendants conservatively, including summaries.
  Open details may preserve actual readable content.
- Repeated/ambiguous attributes cannot override earlier hidden
  declarations; any recognized hiding attribute suppresses the subtree.
- Excluded subtrees leave newline quote boundaries, so discarding a hidden
  negation cannot accidentally join surrounding visible words into a forged
  sentence that was never present as a continuous observed excerpt.

The parser tracks suppressed subtrees, handles common HTML void elements
without trapping subsequent legitimate content, and caps nesting at 256
elements with a clear fail-closed error. Malformed subtrees are conservatively
unwound by matching end tags. Ordinary inline formatting (`strong`,
`span` etc.) remains eligible for exact-text comparison.

**No weakening** was made to exact operator allowlists, DNS/IP pinning,
TLS hostname verification, redirect denial, content-type/UTF-8 rules,
five-second socket timeout, raw and decompressed response byte ceilings,
capture SHA256 or UTC timestamp provenance. The source byte hash is still
computed over response bytes, not a reconstructed "visible" page.

## Tests and measurable acceptance

- `backend/tests/test_step224.py`: parameterized hidden-content
  regressions, whole strict Reality State construction using a **fake**
  backend-owned HTTPS transport, a legitimate visible-quote control,
  HTML void/self-closing/malformed nesting checks, gzip interaction, and
  plain-text non-HTML parity.
- `backend/app/evaluation/html_visibility_quality_benchmark.py`:
  a deliberately **synthetic** eleven-case fixture battery (10 concealed-text,
  1 visible-text case), with expected classifications and explicit
  accuracy-nonclaims.
- The full Python 3.13 workflow invokes this benchmark alongside preserved
  Step 217, Step 218, Step 220 and Step 223 replays.
- The separate existing [Step 222 live-source workflow](../.github/workflows/step222-live-source-smoke.yml)
  must still pass using a real HTTPS publisher capture and the Step 223
  stale-caller-timestamp oracle.

Synthetic results test the restricted parser policy, **not** a representative
real-world corpus of publishers, browser-rendered screenshots, semantic support
or factual accuracy. Unit tests operate on fake source HTML; only the retained
live canary reaches an actual publisher.

## Reproduce

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
python -m backend.app.evaluation.capture_freshness_benchmark
python -m backend.app.evaluation.html_visibility_quality_benchmark
```

The Step 222 HTTPS workflow provides a separate network-only check; do not
disable it or weaken its URL/DNS/TLS controls to satisfy this milestone.

## Limitations, deliberately preserved

This filter is **not a browser engine**, cannot execute external stylesheets,
CSS layout, CSS custom properties, JavaScript, Shadow DOM or all HTML5 error
correction rules. It does not know whether content is visually clipped,
off-screen, hidden by a parent stylesheet, behind accessibility overlays or
displayed differently to different users. Treat parser matching as an
**independent text-presence observation with conservative suppression**, not
verified *human visibility*. The server does not archive raw publisher HTML.
Sources can still publish false claims; there is no publisher signature,
semantic entailment, contradiction understanding or universal factual truth.

## Hosted acceptance

Requires final feature SHA green Python 3.13 full regressions + all prior
benchmark replays + new synthetic benchmark, and separate true-live HTTPS
publisher canary. Then require both again on independently merged `main`,
and repeat on final status-sync `main` commit. Do not award completion based
on synthetic fixtures alone.

## Verified evidence

Pending final hosted feature/merge/status-sync verification.
