# Step 159 — Source Freshness Contract Validation

## Objective

Harden the existing source-freshness result boundary immediately after Step 158 source-observation validation.

## Why This Is the Correct Next Boundary

The existing Reality Layer pipeline observes retrieved sources and then evaluates observation age against an explicitly supplied freshness window. Step 159 therefore validates the canonical `SourceFreshnessResult` produced by that existing evaluator.

## Scope

Step 159 validates:

- freshness result status;
- assessment collection shape;
- nested `SourceFreshnessAssessment` fields;
- source count and assessment-count consistency;
- fresh/stale/unknown count consistency;
- freshness execution state;
- unavailable-result reasons;
- status/assessment consistency.

`SourceFreshnessResultNormalizer` accepts either the canonical result or a compatible mapping and routes mapping-shaped results through the canonical validator.

The production `SourceFreshnessEvaluator.evaluate_result()` now routes unavailable, empty, and usable results through the canonical normalizer. Existing age calculation and the explicit-window requirement are preserved.

## Safety Invariant

retrieval result
→ retrieval validation
→ consumption validation
→ evidence normalization
→ evidence validation
→ evidence consumption validation
→ evidence quality validation
→ claim extraction validation
→ claim-evidence linking validation
→ claim conflict validation
→ source provenance validation
→ source observation validation
→ source freshness validation

## Semantic Boundary

Freshness remains an observation-age assessment, not a truth or authority judgment. If no explicit freshness window is supplied, the existing evaluator continues to return `unknown` with `freshness_window_not_declared`.

Step 159 does not add a new retrieval provider, network behavior, LLM, RAG system, embedding/vector database, semantic truth judge, ML/DL model, or training.

## Validation Truth

Dedicated Step 159 regression tests cover canonical acceptance, mapping normalization, required-field rejection, count consistency, evaluator integration, and preservation of the unknown state when no freshness window is declared. Local pytest execution is still required before claiming a local runtime test pass.
