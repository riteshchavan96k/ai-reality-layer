# Step 129 — Source Freshness Evaluation Boundary

## Objective

Step 129 introduces an explicit source-freshness evaluation boundary after source observation metadata. It evaluates the age of an observed source only when the retrieval request declares an explicit maximum acceptable observation age.

## Pipeline position

`Retrieval → Evidence Normalization → Evidence Quality → Claim Extraction → Claim-to-Evidence Linking → Source Provenance Identity → Source Observation Metadata → Source Freshness Evaluation → Grounding Context`

## Design

- `SourceFreshnessAssessment` is immutable and records source identity, freshness state, observation time, measured age, declared maximum age, method, and an uncertainty reason when required.
- `SourceFreshnessResult` is the canonical aggregate contract with fresh/stale/unknown counts.
- `SourceFreshnessEvaluator` accepts canonical or dictionary-shaped observation results and preserves the existing dictionary compatibility pattern.
- A missing freshness window produces `unknown`, never `fresh`. This prevents the system from treating a newly observed source as proof that the underlying information is current.
- An explicit window classifies observation age as `fresh` when age is within the window and `stale` when it exceeds it.
- The retrieval request now carries optional `freshness_max_age_seconds`, validated as a positive number when supplied.
- Freshness assessment is recorded in orchestration analysis and the existing `reality_retrieval` record and is visible in the execution trace.

## Important semantic boundary

Observation time is not publication time, update time, or truth time. Therefore Step 129 does not claim that a source is factually current merely because it was retrieved recently. It measures the recency of the system's observation against an explicitly declared window. Source publication/update metadata and stronger freshness policies remain separate future concerns.

## Safety behavior

Unavailable or empty observation results propagate to unavailable or empty freshness results. Invalid windows, naive clocks, future observations, and inconsistent contracts fail deterministically rather than producing a freshness claim.

## Explicit non-goals

This step does not add external web access, provider credentials, publication-date extraction, semantic freshness inference, conflict detection, confidence scoring, RAG, embeddings, vector databases, ML training, or LLM integration.

## Validation

Dedicated regression coverage is included in `backend/tests/test_step129.py`. GitHub status checks are not configured. Local pytest execution is still required before claiming a local test pass.
