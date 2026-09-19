# Step 151 — Retrieval Result Consumption Contract Validation

## Objective

Harden the retrieval-result consumption decision itself so typed and mapping-based consumption outcomes are validated through one canonical contract boundary.

## Problem Found

Step 150 validated the retrieval-result envelope before the retrieval consumer classified it. The next downstream boundary was RetrievalResultConsumptionNormalizer, which reconstructed the consumption dataclass directly from mapping keys. That duplicated construction logic and left the contract without an explicit validation entry point.

## Implementation

Step 151 adds RetrievalResultConsumption.validate().

The validator:

- accepts an existing canonical RetrievalResultConsumption unchanged;
- requires the canonical mapping fields;
- delegates status, retrieval-status, boolean, usability, and reason invariants to the dataclass contract;
- returns the canonical typed consumption decision.

RetrievalResultConsumptionNormalizer now delegates mapping normalization to this validator.

The retrieval-result consumer remains responsible only for classifying a validated retrieval result. A duplicate import was also removed.

## Safety Invariant

retrieval result
→ canonical retrieval-result validation
→ consumption classification
→ canonical consumption validation

A malformed consumption decision cannot be silently reconstructed outside the consumption contract.

## Regression Coverage

Dedicated Step 151 tests cover:

- canonical contract acceptance;
- compatible mapping normalization;
- missing required fields;
- status/usability inconsistency;
- invalid boolean values through the normalizer;
- preservation of an existing canonical contract.

## Scope Discipline

No new network behavior, providers, credentials, LLM, RAG, embeddings/vector databases, semantic truth verification, ML/DL, or model execution is introduced.

## Validation Truth

Dedicated regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
