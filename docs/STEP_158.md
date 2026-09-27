# Step 158 — Source Observation Contract Validation

## Objective

Harden the existing source-observation boundary immediately downstream of Step 157 source provenance validation.

## Why This Is the Correct Next Boundary

The existing orchestration pipeline builds canonical source provenance and then constructs source observations from those stable source identities before evaluating source freshness. `SourceObservation` and `SourceObservationBuilder` already exist in the repository; Step 158 therefore validates and hardens that existing boundary rather than inventing a new product subsystem.

## Scope

Step 158 validates:

- observation result status;
- observation collection shape;
- nested `SourceObservation` fields;
- source-count consistency;
- observation execution state;
- unavailable-result reasons;
- ISO-8601 observation timestamps with timezones;
- prevention of future observation timestamps;
- canonical normalization of mapping-shaped results.

The production `SourceObservationBuilder.build_result()` now routes every result-producing branch through `SourceObservationResultNormalizer`.

## Safety Invariant

retrieval result
→ retrieval-result validation
→ retrieval consumption validation
→ evidence normalization
→ evidence-normalization validation
→ evidence normalization consumption
→ evidence quality validation
→ claim extraction validation
→ claim-evidence linking validation
→ claim conflict validation
→ source provenance validation
→ source observation validation
→ source freshness evaluation

## Design Boundary

Source observation records when the retrieval pipeline observed a stable source identity. It does not establish source authority, factual truth, freshness itself, relevance, or semantic agreement. Freshness remains a separate downstream evaluation stage.

## Product Scope Discipline

No LLM, RAG system, embedding model, vector database, ML/DL model, new retrieval provider, or model training is introduced by this step.

## Validation Truth

Dedicated Step 158 regression tests cover canonical acceptance, mapping normalization, malformed result rejection, future timestamp rejection, and production builder integration. Local pytest execution remains required before claiming a full repository test pass. GitHub status checks are not configured.
