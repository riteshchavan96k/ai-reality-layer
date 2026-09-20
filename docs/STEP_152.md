# Step 152 — Evidence Normalization Contract Validation

## Objective

Harden the evidence-normalization contract immediately after retrieval-consumption validation so typed and mapping-shaped evidence-normalization results have one canonical validation entry point.

## Problem Found

The existing `EvidenceNormalizationResult` dataclass validated values when constructed, but its `from_mapping()` helper reconstructed the contract directly. There was no explicit validation entry point for an already-existing evidence-normalization result or mapping.

## Implementation

Step 152 adds `EvidenceNormalizationResult.validate()`.

The validator:

- accepts an existing canonical `EvidenceNormalizationResult` unchanged;
- requires the canonical contract fields for mapping input;
- delegates status, source shape, source count, content presence, and execution-state invariants to the contract constructor;
- returns the canonical typed evidence-normalization result.

`from_mapping()` now delegates through this validator instead of duplicating direct construction.

## Safety Invariant

retrieval result
→ canonical retrieval-result validation
→ consumption classification
→ canonical consumption validation
→ evidence normalization
→ canonical evidence-normalization validation

A malformed evidence-normalization result cannot bypass the contract's existing invariants through the mapping helper.

## Regression Coverage

Dedicated Step 152 coverage tests:

- canonical contract acceptance;
- compatible mapping validation;
- missing required fields;
- inconsistent content-presence state;
- inconsistent source-count state.

## Scope Discipline

No new network behavior, providers, credentials, LLM, RAG, embeddings/vector databases, semantic truth verification, ML/DL, or model execution is introduced.

## Validation Truth

Dedicated regression tests are committed. Local pytest execution is not performed in this workflow unless explicitly run and reported. GitHub status checks are not configured, so no automated test-pass claim is made.
