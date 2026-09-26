# Step 154 — Claim Extraction Contract Validation

## Objective

Harden the claim-extraction boundary immediately after Step 153 so typed and mapping-shaped claim-extraction results have one canonical validation path before downstream claim/evidence linking and conflict analysis.

## Why This Is the Correct Next Boundary

Step 153 completed canonical validation of evidence-normalization consumption. The next downstream object created by the existing orchestration pipeline is `ClaimExtractionResult`. The pipeline already extracts claims immediately after evidence-quality validation and then passes that result into claim/evidence linking and conflict detection.

Step 154 therefore strengthens the existing claim-extraction boundary without changing the product roadmap or introducing a new capability.

## Implementation

Step 154:

- adds `ClaimExtractionResult.validate()`;
- accepts an existing canonical `ClaimExtractionResult` unchanged;
- validates required result fields;
- reconstructs nested `EvidenceClaim` values from compatible mappings;
- preserves the existing claim/result invariants enforced by the dataclasses;
- adds `ClaimExtractionResultNormalizer` for typed or mapping-shaped results;
- routes `EvidenceClaimExtractor.extract_result()` through the canonical normalizer;
- adds dedicated Step 154 regression coverage.

## Safety Invariant

retrieval result
→ retrieval-result validation
→ retrieval consumption validation
→ evidence normalization
→ evidence-normalization validation
→ evidence normalization consumption validation
→ evidence quality validation
→ claim extraction canonical validation
→ downstream claim/evidence linking

A malformed mapping-shaped claim-extraction result cannot bypass the canonical claim-extraction contract when normalization is used.

## Scope Discipline

No new network behavior, provider, credential, LLM, RAG, embedding, vector database, semantic truth verification, ML/DL model, or model execution is introduced.

Existing deterministic sentence-based claim extraction remains unchanged; this step hardens its contract boundary only.

## Validation Truth

Dedicated Step 154 regression tests are committed. Local pytest execution must still be performed in the development environment before claiming the tests pass. GitHub status checks are not configured.
