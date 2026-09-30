# Step 169 — Quality Recovery Execution Outcome Contract Integration

## Objective

Close the model-execution contract bypass in evaluation-guided quality recovery so that any recovery execution selected to replace the primary execution is a canonical `ModelExecutionResult`.

## Why this is the correct next step

After Step 168 restored orchestration import integrity, repository inspection traced the active success path through evaluation and quality recovery.

Step 164 already established a canonical provider-neutral `ModelExecutionResult` with required attempt accounting, fallback metadata, result/error exclusivity, and budget consistency. Primary execution uses that contract.

The recovery implementation did not.

When an alternative recovery model produced a better response, `recover_with_evaluation()` could return a smaller execution dictionary without `attempts_by_model` or `fallback_used`. The orchestration pipeline then replaced `state.execution` with that recovery dictionary, while `_success_result()` unconditionally reads those canonical fields.

That created a real downstream failure path specifically when quality recovery improved the response.

## Implementation

Step 169 routes successful recovery executions through the existing Step 164 model-execution contract.

### Shared attempt accounting

Recovery now seeds per-model attempt accounting from the shared `ExecutionBudget` and the primary execution metadata.

- Canonical primary executions preserve their existing `attempts_by_model` map.
- Compatibility callers that do not provide canonical per-model accounting are normalized against the shared budget when possible.
- Every recovery attempt increments both the shared budget and the corresponding model count.
- The canonical contract verifies that per-model counts equal total attempts and do not exceed the budget.

### Provider recovery path

Successful provider-based recovery now creates a `ModelExecutionResult` and passes it through `ModelExecutionResultNormalizer` before it can become the best execution.

### Legacy adapter recovery path

Successful legacy adapter recovery is normalized through the same canonical execution contract before it can replace the primary result.

### Fallback metadata

A selected alternative recovery model sets `fallback_used=True`, while preserving any existing fallback signal from the primary execution.

## Compatibility

The recovery decision algorithm is unchanged:

- passing initial evaluations still skip recovery;
- candidate order is unchanged;
- blocked providers still consume no attempts;
- provider failures still consume retry budget;
- a recovery candidate only replaces the primary result when its evaluation score is better;
- recovery still stops early on a passing evaluation.

The change is limited to the shape and integrity of a recovery execution that is eligible to replace primary execution.

## Regression coverage

`backend/tests/test_step169.py` verifies:

1. provider recovery with a retry produces a canonical execution result;
2. attempt counts from primary and recovery execution remain consistent;
3. legacy adapter recovery also produces the canonical Step 164 result;
4. alternative recovery correctly records fallback use; and
5. a recovered execution can flow through the pipeline success-response builder without missing canonical fields.

## Safety invariant

canonical primary execution → evaluation → bounded quality recovery → canonical recovery execution outcome → optional replacement of primary execution → outcome memory / final orchestration result.

Quality recovery remains an optimization mechanism. A better evaluation score does not establish factual truth, grounding correctness, model superiority, or a calibrated probability.

## Design boundary

This step hardens recovery execution integrity only. It does not change retrieval, evidence, provenance, freshness, conflict detection, confidence signals, grounding authorization, evaluation methodology, routing policy, provider credentials, network behavior, RAG, embeddings, ML/DL training, or truth inference.

## Validation truth

Dedicated Step 169 regression coverage is committed. Repository structure and final Git diff are verified in this workflow. Test execution is reported separately and is never inferred from the presence of test files.
