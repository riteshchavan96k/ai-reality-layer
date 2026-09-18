# Step 130 — Claim Conflict Detection Boundary

## Objective

Step 130 introduces a deterministic boundary for identifying explicit candidate conflicts among extracted claims. This makes disagreement observable before later confidence and Reality State construction.

## Pipeline position

`Retrieval → Evidence Normalization → Evidence Quality → Claim Extraction → Claim-to-Evidence Linking → Claim Conflict Detection → Source Provenance → Source Observation → Source Freshness → Grounding`

## Detection semantics

The detector currently recognizes only an explicit negation pair: a normalized claim and the same normalized claim prefixed by `not`, `no`, or `never`. It does not infer semantic contradiction, factual correctness, causality, numerical disagreement, or source reliability.

A detected conflict is therefore a **candidate conflict**, not proof that either claim is false.

## Integration

- Adds immutable `ClaimConflict` and `ClaimConflictResult` contracts.
- Adds `ClaimConflictDetector` with canonical and dictionary APIs.
- Injects the detector through `OrchestrationDependencies`.
- Records the result in orchestration analysis and the existing `reality_retrieval` record.
- Records conflict count and status in the execution trace.
- Detection is observational and does not block model execution. Existing evidence-quality and grounding/authorization gates remain authoritative.

## Safety boundary

Unavailable or empty claim extraction propagates to the corresponding conflict result. Invalid contract shapes fail deterministically. No conflict is invented from URL similarity, source ordering, titles, or general semantic resemblance.

## Explicit non-goals

No LLM contradiction judge, embeddings, vector search, external retrieval, source reliability scoring, confidence scoring, truth verification, ML training, or DL training is introduced by this step.

## Validation

Dedicated regression coverage is in `backend/tests/test_step130.py`. GitHub status checks are not configured, and local pytest execution has not been performed in this session; therefore no test-pass claim is made.
