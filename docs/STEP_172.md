# Step 172 — Orchestration Result Contract Validation

## Objective

Add a canonical contract for every terminal result returned by the orchestration pipeline and exposed through the public `orchestrate_task()` / `/api/v1/solve` path.

## Why this is the correct next step

Steps 164–171 progressively established canonical boundaries for the internal execution path:

- model execution outcome;
- execution trace event/snapshot;
- outcome memory;
- quality-recovery execution;
- response evaluation; and
- the complete quality-recovery envelope.

After Step 171, the next unvalidated boundary was the outer orchestration result itself.

`OrchestrationPipeline.run()` still returned one of six hand-built dictionaries:

- `awaiting_human_approval`;
- `retrieval_unavailable`;
- `grounding_unavailable`;
- `execution_context_unavailable`;
- `execution_failed`; or
- `orchestrated`.

`orchestrate_task()` returned that dictionary directly, `process_task()` passed it through, and the FastAPI `/api/v1/solve` endpoint returned it without a response model.

Step 172 therefore closes the public orchestration-envelope integrity gap rather than introducing another internal micro-contract.

## Canonical contract

Step 172 introduces:

- immutable `OrchestrationResult`; and
- `OrchestrationResultNormalizer`.

The contract preserves the existing flattened dictionary API:

```
{
  "status": ...,
  ...status-specific fields...
}
```

Unknown extension fields remain preserved.

## Supported terminal statuses

The canonical contract explicitly recognizes the six statuses currently produced by the pipeline:

1. `awaiting_human_approval`;
2. `retrieval_unavailable`;
3. `grounding_unavailable`;
4. `execution_context_unavailable`;
5. `execution_failed`;
6. `orchestrated`.

Each status has its own required top-level field set.

This prevents a terminal status from being returned with a structurally unrelated or incomplete payload.

## Common boundary validation

Every terminal result validates:

- analysis mapping;
- routing mapping;
- approval mapping; and
- execution trace snapshot.

Trace validation is routed through the existing Step 166 canonical execution-trace snapshot boundary.

## Blocked/unavailable outcomes

Retrieval, grounding, and execution-context unavailable responses continue to preserve their existing dictionary shapes.

The `retrieval_unavailable` branch additionally validates its public grounding envelope through the existing canonical grounded-result contract.

Other internal grounding/context mappings remain status-specific diagnostic state and are validated as mappings rather than falsely reclassified as grounded-result envelopes.

## Execution failure

The `execution_failed` terminal result now requires:

- a canonical Step 164 failed `ModelExecutionResult`;
- a canonical Step 167 `OutcomeMemoryRecord`; and
- a failed execution status in both objects.

No fabricated answer or evaluation is introduced.

## Successful orchestration

The public success envelope validates:

- execution summary integrity;
- result mapping;
- canonical grounded-result envelope;
- canonical Step 170 response evaluation;
- canonical Step 171 quality-recovery envelope;
- canonical selected Step 164 recovery execution;
- canonical Step 167 outcome-memory record; and
- canonical Step 166 trace snapshot.

### Cross-object consistency

Step 172 does more than validate nested objects independently.

The successful terminal envelope requires the following objects to describe the same selected outcome:

- quality-recovery best model;
- quality-recovery best execution;
- top-level execution summary;
- top-level evaluation;
- returned model result; and
- stored outcome-memory record.

It verifies selected-model identity, execution attempt totals, budget limit, per-model attempt accounting, fallback flag, selected evaluation score, outcome execution status, and outcome evaluation score.

This prevents a structurally valid but internally contradictory public response.

## Execution summary

The public API historically exposes a reduced execution summary rather than the complete internal `ModelExecutionResult`.

Step 172 preserves that API shape instead of adding internal `result` / `errors` fields.

The summary contract validates:

- successful status;
- non-empty model;
- attempts;
- total attempts;
- budget limit;
- per-model attempt counts; and
- fallback flag.

## Integration

### Pipeline terminal builders

All six terminal-result helper methods now route their dictionaries through `OrchestrationResultNormalizer` before returning.

### Public orchestration entry point

`orchestrate_task()` additionally normalizes the result returned by `pipeline.run()` before exposing it.

This defense-in-depth boundary protects the public orchestration API if a future pipeline path accidentally returns an unvalidated envelope.

`process_task()` and `/api/v1/solve` therefore receive the canonical dictionary without changing their existing external interface.

## Compatibility

Step 172 does not change:

- terminal status names;
- public dictionary shapes;
- execution control flow;
- approval behavior;
- retrieval behavior;
- grounding decisions;
- retry/fallback policy;
- recovery ranking;
- evaluation methodology;
- outcome-memory semantics; or
- Reality State generation.

It only validates the result already produced by those systems.

## Safety invariant

canonical pipeline stages
→ canonical model execution
→ canonical evaluation
→ canonical recovery
→ canonical outcome memory / trace / grounding
→ canonical terminal orchestration result
→ public `orchestrate_task()`
→ `/api/v1/solve`.

A canonical orchestration result means the response is structurally and internally consistent with the project's declared contracts. It is not a certificate that model text is factually true, semantically correct, safe for every use, or perfectly grounded.

## Design boundary

Step 172 is a public-result integrity step only.

It does not add:

- a new LLM/provider;
- credentials;
- external network behavior;
- RAG;
- embeddings/vector search;
- model training;
- new retrieval sources;
- semantic truth inference;
- new confidence methodology; or
- new product features.

## Regression coverage

`backend/tests/test_step172.py` covers:

1. every non-execution terminal status;
2. execution-failure result validation;
3. canonical successful orchestration;
4. extension metadata preservation;
5. unsupported terminal status rejection;
6. missing status-specific fields;
7. malformed execution traces;
8. recovery-selected model mismatch;
9. selected-execution attempt mismatch;
10. selected-evaluation mismatch;
11. outcome-memory model mismatch;
12. outcome-memory attempt mismatch;
13. returned-result model mismatch; and
14. public `orchestrate_task()` compatibility.

## Validation truth

Dedicated Step 172 regression coverage is committed. Repository structure and the final Git diff are verified in this workflow. A targeted pytest run covering Steps 172, 171, 170, 169, and 23 was attempted from a fresh checkout, but the available runtime could not resolve `github.com`; the clone failed before pytest started. No automated test-pass claim is made.
