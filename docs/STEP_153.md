# Step 153 — Evidence Normalization Consumption Contract Validation

## Objective

Harden the evidence-normalization consumption boundary immediately after Step 152 so typed and mapping-shaped consumption decisions have one canonical validation path before downstream evidence quality validation.

## Problem Found

Step 152 established canonical validation for EvidenceNormalizationResult. The next downstream boundary was EvidenceNormalizationConsumption. Its dataclass already enforced invariants during direct construction, but there was no explicit validation entry point or normalizer for an existing mapping-shaped consumption decision.

That left the boundary less explicit than the retrieval-result and earlier consumption contracts.

## Implementation

Step 153:

- adds EvidenceNormalizationConsumption.validate();
- accepts an existing canonical consumption contract unchanged;
- requires the canonical mapping fields;
- delegates status, evidence-status, boolean, usability, and reason invariants to the contract;
- adds EvidenceNormalizationConsumptionNormalizer;
- injects that normalizer through OrchestrationDependencies;
- routes pipeline consumption results through the canonical normalizer before downstream use;
- adds dedicated Step 153 regression coverage.

## Safety Invariant

retrieval result
→ canonical retrieval-result validation
→ retrieval consumption
→ canonical retrieval-consumption validation
→ evidence normalization
→ canonical evidence-normalization validation
→ evidence normalization consumption
→ canonical evidence-normalization-consumption validation
→ evidence quality validation

A malformed evidence-normalization consumption decision cannot bypass the contract boundary when the pipeline receives a typed result or compatible mapping.

## Regression Coverage

Dedicated Step 153 tests cover:

- canonical contract acceptance;
- compatible mapping normalization;
- missing required fields;
- status/usability inconsistency;
- unsupported evidence status.

## Scope Discipline

No new network behavior, providers, credentials, LLM, RAG, embeddings/vector databases, semantic truth verification, ML/DL, or model execution is introduced.

## Validation Truth

Dedicated regression tests are committed. Local pytest execution has not been performed in this workflow. GitHub status checks are not configured, so no automated test-pass claim is made.
