# Step 87 — Evidence Normalization Contract

## Objective

Establish a stable typed contract for the output of retrieval-evidence normalization before evidence quality validation and grounding.

## Implementation

- Added `EvidenceNormalizationResult` in `backend/app/reality/evidence_normalization.py`.
- The contract captures normalized status, provenance-preserving sources, content, source count, content presence, and normalization execution state.
- Added validation for supported status values and internal consistency.
- Added `RetrievalEvidenceNormalizer.normalize_result()` as the canonical typed boundary.
- Preserved `normalize()` as a compatibility dictionary API backed by the typed contract.
- Updated `OrchestrationPipeline` to consume `normalize_result()` and serialize the contract before quality validation.
- Added dedicated Step 87 regression tests.

## Design Boundary

The flow is:

`retrieval result → evidence normalization result contract → evidence quality validation`

This step does not introduce external providers, network access, credentials, RAG, embeddings/vector search, factual verification, semantic evaluation, citation generation, ML training, or LLM integration.

## Validation Truth

Regression tests are included but local execution has not been performed in this session. GitHub Actions workflow runs are not available for the merge commit, so no test pass is claimed.
