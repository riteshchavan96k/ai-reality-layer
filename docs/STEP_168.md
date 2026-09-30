# Step 168 — Orchestration Stage Contract Restoration and Import Integrity

## Objective

Restore the missing `OrchestrationStageContext` module required by the active orchestration pipeline and re-establish the Step 59 stage-context invariant without changing orchestration semantics.

## Why this is the correct next step

Repository verification after Step 167 found a concrete integrity break:

- `PROJECT_STATUS.md` records Step 59 as adding a shared `OrchestrationStageContext` for orchestration state, trace, and execution budget.
- `backend/app/orchestrator/pipeline.py` actively imports and uses `backend.app.orchestrator.stage_contract.OrchestrationStageContext`.
- `backend/tests/test_step59.py` also imports and tests that contract.
- The corresponding `backend/app/orchestrator/stage_contract.py` file was absent from `main`.

Git history shows the contract existed during Step 59 work, was removed by an isolation/cleanup commit, and the pipeline was then integrated to depend on it. That left the default branch with an unresolved import even though later contract work continued.

Step 168 therefore repairs an existing architectural invariant before any new feature or contract expansion.

## Implementation

- Restores `backend/app/orchestrator/stage_contract.py` with the original Step 59 contract semantics.
- Preserves the mutable `OrchestrationState`, trace reference, and optional shared `ExecutionBudget`.
- Preserves `set_budget()` for establishing/replacing the shared budget.
- Preserves `require_budget()` and its fail-closed behavior when a budget has not been established.
- Makes no changes to routing, retrieval, grounding, model execution, evaluation, recovery, tracing, or outcome-memory behavior.

## Regression coverage

`backend/tests/test_step168.py` verifies:

1. the orchestration pipeline can import the restored stage contract;
2. state, trace, and execution budget references are preserved;
3. replacing the shared budget does not replace orchestration state; and
4. budget-dependent stages fail closed when no budget exists.

The earlier Step 59 regression coverage remains intact.

## Safety invariant

Orchestration state + trace + shared execution budget → explicit stage context → pipeline stages.

The stage context is an execution-coordination container only. It does not create evidence, establish factual truth, authorize model execution by itself, alter grounding decisions, or change model-selection semantics.

## Compatibility

This is a restoration of the contract already referenced by the pipeline and historical Step 59 tests. It intentionally avoids changing public orchestration return shapes or introducing new runtime behavior.

## Validation truth

Dedicated Step 168 regression coverage is committed. This workflow verifies repository structure, history, imports by static dependency inspection, and final Git diff. Local pytest execution is not available in this GitHub-only workflow, and GitHub status checks are not configured, so no automated test-pass claim is made.
