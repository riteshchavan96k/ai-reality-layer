# Step 148 — Not-Required Retrieval Result Contract

## Objective

Make the retrieval engine's `not_required` outcome use the same canonical retrieval-result contract as completed, failed, and blocked outcomes.

## Problem Found

Before Step 148, `RealityRetrievalEngine` constructed its `not_required` result as an ad-hoc dictionary. The canonical `RetrievalResultContract` did not define `not_required`, even though `RetrievalResultConsumer` already recognized that status.

This created two representations of the same pipeline state:

- canonical validation for provider-backed retrieval outcomes;
- an unvalidated hand-built dictionary for the no-retrieval path.

That inconsistency weakened the result boundary and allowed the engine's no-retrieval path to bypass the contract's validation rules.

## Implementation

Step 148:

- adds `RetrievalResultContract.not_required()`;
- extends canonical status validation to include `not_required`;
- requires the no-retrieval result to have:
  - `provider=None`;
  - empty `sources`;
  - `content=None`;
  - `retrieval_executed=False`;
  - no `reason`;
- keeps the request as part of the result envelope;
- changes `RealityRetrievalEngine` to return the canonical contract instead of an ad-hoc dictionary;
- validates that a `not_required` engine result still has a dictionary request.

No provider is selected or executed for this status.

## Safety Invariant

`not_required → provider=None, empty payload, retrieval_executed=False`

Therefore the no-retrieval path cannot claim that retrieval occurred or carry retrieval payload data.

## Regression Coverage

Dedicated Step 148 tests cover:

- canonical `not_required` result shape;
- rejection of an unexpected provider;
- rejection of sources/content payloads;
- rejection of an unexpected reason;
- rejection of an execution claim;
- engine use of the canonical contract;
- missing-request rejection.

## Scope Discipline

This step does not add:

- network behavior;
- providers or endpoints;
- credentials or secrets;
- LLM integration;
- RAG;
- embeddings or vector databases;
- semantic truth verification;
- ML/DL training;
- model execution.

## Validation Truth

Dedicated regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
