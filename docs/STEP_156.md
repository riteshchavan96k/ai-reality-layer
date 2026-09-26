# Step 156 — Claim Conflict Contract Validation

## Objective

Harden the next existing downstream Reality Layer boundary after Step 155: the canonical result produced by claim-conflict detection.

## Why This Is the Correct Next Boundary

The existing orchestration pipeline performs claim extraction, claim-evidence linking, and then deterministic claim-conflict detection before source provenance, observation, freshness, confidence aggregation, and Reality State assembly.

Step 154 established the claim-extraction validation boundary. Step 155 established the claim-evidence-linking validation boundary. Step 156 therefore hardens the immediately downstream `ClaimConflictResult` boundary without introducing a new product capability.

## Scope

Step 156 validates:

- result status;
- conflict collection shape;
- nested `ClaimConflict` fields;
- claim count;
- conflict count and collection consistency;
- detection execution state;
- unavailable-result reasons;
- status/conflict consistency.

`ClaimConflictResultNormalizer` accepts either the canonical result or a compatible mapping and routes mapping-shaped results through the canonical validator.

The production `ClaimConflictDetector.detect_result()` now routes every result-producing branch through the canonical normalizer. Existing deterministic conflict detection behavior is unchanged.

## Safety Invariant

retrieval result
→ retrieval-result validation
→ retrieval consumption validation
→ evidence normalization
→ evidence-normalization validation
→ evidence normalization consumption validation
→ evidence quality validation
→ claim extraction validation
→ claim-evidence linking validation
→ claim conflict validation
→ downstream provenance/freshness/confidence/Reality State processing

## Semantic Boundary

The detector continues to recognize only explicit deterministic negation pairs. A conflict remains a candidate conflict and is not a factual-truth judgment.

Step 156 does not add semantic contradiction inference, an LLM contradiction judge, embeddings, vector search, source reliability scoring, or truth verification.

## Product Scope Discipline

No new retrieval provider, network behavior, credentials, LLM, RAG system, embedding model, vector database, ML/DL model, or model training is introduced by this step.

## Validation Truth

Dedicated Step 156 regression tests cover canonical acceptance, mapping normalization, malformed result rejection, nested conflict validation, count consistency, and production detector integration. Local pytest execution remains required before claiming a full repository test pass. GitHub status checks are not configured.
