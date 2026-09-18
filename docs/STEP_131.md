# Step 131 — Reality Confidence Signal Boundary

## Objective

Step 131 aggregates the evidence, claim-linking, freshness, and conflict signals already produced by the Reality Layer into one explicit confidence-signal profile.

## Important semantic boundary

This is **not a calibrated probability** and does not claim that a claim is true. It is a deterministic support/uncertainty signal derived from existing structural evidence signals. Calibration and learned confidence remain future work.

## Signals

- Evidence quality must be usable before the profile can be supported.
- Claim/evidence coverage is represented as linked claims divided by extracted claims when claims exist.
- Missing extracted claims are treated as uncertainty rather than support.
- Stale or unavailable freshness creates uncertainty.
- Candidate conflicts create uncertainty; they are not resolved by this step.
- Unavailable claim/evidence linking or conflict detection creates uncertainty.

## Pipeline position

`Retrieval → Evidence Normalization → Evidence Quality → Claim Extraction → Claim-to-Evidence Linking → Conflict Detection → Provenance → Observation → Freshness → Confidence Signals → Grounding`

## Integration

The aggregator is dependency-injected and records its canonical result in orchestration analysis, the existing `reality_retrieval` record, and the execution trace. It does not alter existing execution authorization gates.

## Explicit non-goals

No arbitrary confidence probability, LLM judge, embedding similarity, source-reliability model, external retrieval, RAG, vector database, ML training, or DL training is introduced.

## Validation

Dedicated regression coverage is in `backend/tests/test_step131.py`. GitHub status checks are not configured and local pytest execution has not been performed in this session, so no test-pass claim is made.
