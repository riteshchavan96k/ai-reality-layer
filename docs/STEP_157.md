# Step 157 — Source Provenance Contract Validation

## Objective

Harden the next existing downstream Reality Layer boundary after Step 156: the canonical result produced by source-provenance construction.

## Why This Is the Correct Next Boundary

The orchestration pipeline performs claim extraction, claim-evidence linking, claim-conflict detection, and then source provenance before source observation, freshness, confidence aggregation, and Reality State assembly.

Step 154 established claim-extraction validation. Step 155 established claim-evidence-linking validation. Step 156 established claim-conflict validation. Step 157 therefore hardens the immediately downstream `SourceProvenanceResult` boundary without introducing a new product capability.

## Scope

Step 157 validates:

- result status;
- provenance source collection shape;
- nested `SourceProvenance` fields;
- source count and collection consistency;
- provenance execution state;
- unavailable-result reasons;
- status/source consistency.

`SourceProvenanceResultNormalizer` accepts either the canonical result or a compatible mapping and routes mapping-shaped results through the canonical validator.

The production `SourceProvenanceBuilder.build_result()` now routes every result-producing branch through the canonical normalizer. Existing deterministic URI identity generation and duplicate-source handling are unchanged.

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
→ source provenance validation
→ source observation
→ freshness
→ confidence
→ Reality State

## Semantic Boundary

Source provenance establishes stable source identity metadata only. It does not establish source authority, factual truth, freshness, relevance, or correctness.

Step 157 does not add an LLM judge, semantic contradiction inference, embeddings, vector search, new retrieval providers, network behavior, source-reliability scoring, ML/DL model execution, or model training.

## Validation Truth

Dedicated Step 157 regression tests cover canonical acceptance, mapping normalization, malformed result rejection, nested provenance validation, source-count consistency, and production builder integration. Local pytest execution remains required before claiming a full repository test pass. GitHub status checks are not configured.
