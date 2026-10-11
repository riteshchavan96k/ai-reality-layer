# Step 229 — Bounded Independent-Source Explicit Counterstatement Guard

## Repository-derived problem and scope

Verified starting point: Step 228 final merged `main` SHA `39cda7748a239e9ced057594db47eb1196d05e17`, with the full backend suite (2,371 tests) and **four genuine HTTPS/CI workflows successful on exactly that commit**. Step 228 ensures one submitted excerpt is a unique, complete text unit in backend-observed source content. However, `independent_source_text_assurance.py` then discards the rest of the independently observed document without screening other structural text units for an explicit opposite statement. In opt-in claim mode the one excerpt can therefore be interpreted as `aligned` despite another whole paragraph in that same observed source explicitly saying the opposite.

**Step 229 is the narrow fix to this observed omission**, not a new generalized semantic or factual truth verifier.

## Implementation

- New `backend/app/reality/source_counterstatement_guard.py` scans the **already retrieved** source text line by line (HTML reader paragraphs, headings, list items and table cells are separated using the Step 225 source-text unit boundaries; plain-text records use lines). It uses only the already bounded Step 227 atomic parser/relationship matcher; no added network, model, external API, browser or arbitrary origin is introduced.
- A counterstatement is detected only when another *complete source unit* forms an explicit opposing atomic proposition: the same entity and predicate but direct positive/negative polarity disagreement, positive release dates with distinct values. Step 228 *already rejects* repeated embedded excerpts such as `It is false that <claim>` before this step runs. That earlier gate is deliberately preserved, not counted as new Step 229 detection. Unsupported language is never asserted to have been semantically analyzed.
- Step 229 applies **only** when the existing request has `require_claim_alignment=true` (which already requires backend-controlled independent source text). The Step 228 unique/whole-unit gate remains mandatory. When an explicit counterstatement is found, assurance fails closed with fixed, non-sensitive code `independent_source_explicit_counterstatement`, no successful digest/time and `source_counterstatement_status=counterstatement_observed`. The Reality State remains `uncertain`, not `supported`.
- The source assurance normally issues `source_counterstatement_status=no_bounded_counterstatement_observed` after all earlier identity, matching, structural-context and capture-metadata gates succeed. The Step 227 claim-alignment evaluator requires this **backend-issued** status before returning `aligned`. This is a negative result of a **limited syntactic scan**, *not* proof that the page is contradiction-free.
- Legacy independent exact-text checking with no claim opt-in is **unchanged** and does not falsely claim a source-wide analysis. Existing URL allowlist/DNS/IP/TLS pinning, no redirects or proxy, body/decompression/time bounds, fixed original publisher canaries, canonical response schema and original Step 226 behavior stay intact.
- Tests run through the actual backend-owned injected reader, orchestrator, and FastAPI route, including direct same-entity denial, alternate single-value release date, stable-release negation, unrelated entity controls, refused metadata injection, no second source read, and no source-body leakage. The Step 229 policy replay is appended to Python 3.13 CI. The unchanged actual Python.org claim canary also checks the new backend-issued counterstatement status.

## Critical limitations / nonclaims

This does **not** solve the whole-page meaning problem: unparseable contradiction, implied negation, quoted claims without obvious markers, later corrections expressed in different words, embedded refutations inside longer paragraphs, modality, multi-hop reasoning, changing entity references, sarcasm, external stylesheet/browser context, disputed facts, or publisher-authored world truth. A result `no_bounded_counterstatement_observed` is only a scan over the recognized finite grammar. Refusing a document with a stated contradiction is conservative; it does not establish which paragraph is correct.

New regression tests and scenario labels are developer-authored synthetic fixtures, not an independently human-labeled representative factual accuracy dataset. A successful live Python.org canary checks one previously reviewed stable-release statement and its direct negation; it does not measure performance across arbitrary publishers, languages, claims, or time periods. No production factual accuracy or general semantic entailment is claimed.

## Reproduction and acceptance

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.source_counterstatement_benchmark
python -m backend.app.evaluation.claim_alignment_benchmark
python -m backend.app.evaluation.observed_context_benchmark
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
python -m backend.app.evaluation.capture_freshness_benchmark
python -m backend.app.evaluation.html_visibility_quality_benchmark
python -m backend.app.evaluation.structural_quote_benchmark
```

Mandatory acceptance: review exact feature diff; pass **all backend tests and all old/new synthetic replays**, real Python.org HTTPS canary, real Python.org + IANA HTTPS canary and Step 227 live source-backed claim-alignment canary on the feature SHA. Merge PR only after those four succeed. Independently verify all four on the new merged `main` SHA. If documentation synchronization follows, independently verify all four once more on the final `main` SHA. Never use merely a green PR UI, mocked transport, fixed toy data or documentation to claim completion.

## Verified status

**Implementation is merged and independently verified on exact `main` SHA `fca91e4525e4f50624f95a0df137e281ce189c85`.** Feature [PR #235](https://github.com/riteshchavan96k/ai-reality-layer/pull/235) merged. GitHub Actions records and backend job logs were checked on that exact implementation SHA:

- [Full Python 3.13 CI 38167957918](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38167957918): compilation and **2,398 tests passed** (`2398 passed in 4.71s`), all historical benchmarks and Step 229 synthetic replay.
- [Original Python.org live HTTPS 38167957899](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38167957899): successful.
- [Python.org + IANA dual-publisher real HTTPS 38167957907](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38167957907): successful.
- [Step 227 genuine Python.org claim HTTPS 38167957903](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/38167957903): successful, original-source context guard and positive/negative claim check retained.

The Step 229 fixed synthetic corpus contains **14 cases: six unrelated/positive aligned, six directly opposing whole-source units refused by Step 229, and two duplicate/embedded opposite units already refused by Step 228**. No false alignments among eight expected refusals. These are handwritten examples, not independently annotated population evaluation. Bounded syntax cannot prove a source contains no disagreement or factual falsehood.

This documentation-only final acceptance synchronization must independently pass the same four workflows on its exact feature SHA, merge, and again pass four post-merge workflows on its own final `main` SHA before awarding complete status.
