# Step 227 — Bounded Atomic Claim Alignment, Strict Evidence Mode

## Verified motivating gap

On Step 226's exact verified merged `main` (`759c2db7c24789e950da48bd5226573ad69b8c66`), the API's optional independent original-source gate established *excerpt presence* via DNS/IP-pinned, HTTPS/TLS-approved original-source retrieval and a digest/time audit. The separate task string and the actual factual proposition were **not** independently compared. An excerpt about a correct release date could be returned as `supported` even when the user was checking a contradictory specific date. The Step 226 scorecard does not measure semantic entailment.

The existing optional `ClaimSemanticStructuringStage` defaults to *not attempted*. It must not be misrepresented as a trained semantic reasoner. A full language-inference engine or domain-wide calibrated factual accuracy is not in scope for this small milestone.

## Scope: actual conservative functionality (not universal semantics)

- New `backend/app/reality/claim_assertion_alignment.py` compares an *explicit, separate client claim* to each independently observed, source-scoped submitted excerpt. Exact server-observed source matching MUST already have succeeded for every source, and every matched source must carry the backend's SHA256 capture and UTC time. Nothing caller-supplied is considered a publisher attestation.
- Deterministic grammar deliberately recognizes only single-sentence atomic forms of a named subject: `X was released on DATE.` and `X is/was [not] PROPERTY.`. It compares subject/predicate/value and bounded grammatical polarity; contradictory named release dates are treated as disagreements only when both are positive statements. Distinct properties are *not* automatically contradictory.
- Sources are evaluated separately. All direct relationships must be aligned for an `aligned` assessment. If all directly contradict, result is `contradicted`; mixed alignments/contradictions yield `conflicting`; any unsupported parse/source ambiguity yields `insufficient`. Any result other than `aligned` forces the canonical state to `uncertain`, without bypassing existing quality, evidence links, explicit entity, capture freshness or conflict checks.
- New `require_claim_alignment: true` API opt-in requires `require_independent_source_text_match: true` and an explicit, bounded `claim_text`. Defaults and historical strict requests are not changed. The server rejects invalid/contradictory optional settings rather than silently claiming verification.
- Result is attached at `evidence.claim_alignment` with per-source decision and `semantic_support_verified=false`, `factual_truth_verified=false`. A positive result means **bounded textual assertion alignment only**. An unconfigured reader always abstains.
- Quote marks, reporting/rumor/hedging vocabulary, multiple sentences, different predicates/entities, unparseable language, missing timestamps/digests and excerpts with embedded newlines fail closed. These heuristics cannot detect every misleading context.

## Live quality boundary

Step 227 changes no HTTP reader, DNS/IP allowlist, certificate or redirect behavior, and does not introduce a network call, external model, LLM dependency, arbitrary URL or model authority. It processes only source-scoped excerpts already matched by existing strict mode.

The original publisher's *larger page context is not cryptographically attested as endorsing the excerpt*. Even a matched, unquoted statement might be part of a quotation, example, mistake, satire or disinformation. This is NOT publisher-authenticated authorship, full semantic entailment, independent truth, or a production-ready fact checker. In particular the unsupported word list and restricted grammar are insufficient for general text, multilingual statements, full HTML context, cross-sentence coreference and scoped negation.

## Reproduction and acceptance

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.claim_alignment_benchmark
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
python -m backend.app.evaluation.capture_freshness_benchmark
python -m backend.app.evaluation.html_visibility_quality_benchmark
python -m backend.app.evaluation.structural_quote_benchmark
```

The new replay uses 16 deliberately handwritten scenarios, **one positive** and 15 adversarial/unrelated examples. Passing these cases is a policy regression test; do not infer statistical generalization, recall, accuracy, real publisher annotation or real-language inference. Unit/in-process FastAPI tests use injected fake source readers; preserve genuine original Python.org and two-publisher original HTTPS separate workflows.

The Step 227 implementation is accepted only after complete Python 3.13 tests and all historical+new replays on feature head, successful genuine single- and two-publisher HTTPS CI, feature PR merge, then all three again on exact final merged-main SHA. Do not mark completion from documentation, mocked observation, a green subset, or PR CI alone.

## Status

Implementation and CI verification pending. Update this section only with exact observed commit/run evidence.
