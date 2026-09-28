# Step 163 — Grounding Context Contract Validation

## Objective

Harden the existing provenance-preserving `GroundingContext` boundary used to prepare evidence for downstream model execution.

Step 162 established validation for the downstream grounded-result envelope. Step 163 closes the adjacent upstream execution-context contract so malformed or internally inconsistent grounding context cannot cross into model execution.

## Scope

Step 163 adds:

- canonical `GroundingContext.validate()` support;
- required-field validation for mapping-shaped contexts;
- source collection normalization and validation;
- source-count consistency validation;
- status/content/source consistency validation;
- explicit `grounding_executed` consistency for ready contexts;
- routing of `GroundingContextNormalizer` through the canonical validator;
- routing of `EvidenceGroundingContextBuilder.build_result()` through the canonical normalizer;
- dedicated Step 163 regression coverage.

The existing `build()` dictionary API remains available.

## Safety Invariant

retrieval → evidence normalization → evidence quality → grounding context validation → model execution → grounded result validation.

The broader evidence/reality pipeline remains responsible for claim, provenance, observation, freshness, confidence, and Reality State controls before the grounded-result boundary.

## Semantic Boundary

A `ready` grounding context means the existing evidence pipeline produced an execution-ready context. It does not mean the evidence is true, authoritative, complete, or probabilistically certain.

`grounding_executed` records execution state; it is not a confidence score.

Step 163 does not add an LLM judge, embeddings, vector database, new retrieval provider, external network behavior, ML/DL model, model training, or semantic truth inference.

## Validation Truth

Dedicated Step 163 regression tests cover canonical acceptance, mapping normalization, required-field rejection, source-count consistency, unavailable-state safety, execution-state consistency, builder integration, and unavailable-path preservation.

Local pytest execution is still required before claiming a local runtime test pass.
