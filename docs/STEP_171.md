# Step 171 — Quality Recovery Result Contract Validation

## Objective

Add a canonical integrity boundary for the complete evaluation-guided quality-recovery result before orchestration trusts recovery metadata, selected model/execution/evaluation, or recovery-attempt accounting.

## Why this is the correct next step

Step 169 made successful recovery executions canonical `ModelExecutionResult` values.

Step 170 then made response evaluations canonical `ResponseEvaluationResult` values.

After those steps, the outer quality-recovery envelope itself remained an unchecked dictionary. The orchestration pipeline still trusted fields such as:

- `used`;
- `reason`;
- `improved`;
- `best`;
- `recovery_attempts`; and
- `candidates_tried`.

The recovery function is injectable, so malformed or internally inconsistent recovery output could influence execution replacement, tracing, or the final orchestration result even when nested execution and evaluation contracts existed.

Step 171 closes that envelope-level integrity gap.

## Canonical contracts

Step 171 introduces:

- immutable `QualityRecoveryBest`;
- immutable `QualityRecoveryResult`; and
- `QualityRecoveryResultNormalizer`.

### QualityRecoveryBest

The selected best candidate must provide:

- a non-empty model identity;
- a successful execution mapping whose model matches the selected model;
- a result mapping; and
- a canonical response evaluation.

The recovery envelope intentionally does not require every historical direct caller's execution mapping to satisfy the full Step 164 execution contract. Older direct recovery tests use lightweight initial execution fixtures. Full Step 164 validation is therefore enforced at the active orchestration consumption boundary, where the pipeline always requires canonical execution state.

### QualityRecoveryResult

The envelope requires:

- `used`: boolean;
- `reason`: non-empty string;
- `improved`: boolean;
- `best`: canonical `QualityRecoveryBest`;
- `recovery_attempts`: non-negative integer;
- `candidates_tried`: sequence of non-empty model names.

Unknown extension metadata is preserved.

## Consistency rules

The canonical envelope enforces that:

- `used` matches whether any candidates were actually reported as tried;
- unused recovery reports zero recovery attempts;
- used recovery reports at least one recovery attempt;
- improved recovery must have used a recovery candidate;
- an improved best model must appear in `candidates_tried`;
- the best execution model matches the selected best model;
- the best execution represents a successful result; and
- the nested best evaluation satisfies the Step 170 response-evaluation contract.

## Built-in recovery integration

`recover_with_evaluation()` now routes both of its public result paths through `QualityRecoveryResultNormalizer`:

1. the initial-evaluation-pass path; and
2. the completed review/recovery path.

The public return type remains dictionary-shaped for compatibility.

Historical lightweight initial execution fixtures remain supported as long as they preserve the recovery envelope's own semantics.

## Orchestration consumption hardening

The active pipeline now treats injected recovery output as untrusted until validated.

After canonical envelope normalization, the pipeline additionally verifies runtime facts that the envelope alone cannot know.

### Shared budget accounting

The pipeline records the shared execution budget before recovery and compares it with the budget after recovery.

The reported:

`recovery_attempts`

must equal the actual shared-budget delta.

This prevents an injected recovery implementation from claiming attempts that were not consumed or hiding attempts that were consumed.

### Candidate integrity

Every reported tried candidate must:

- belong to the candidate set supplied by orchestration; and
- differ from the model that produced the initial successful execution.

### Improvement integrity

The `improved` flag must match whether the selected best model actually differs from the initial execution model.

### Canonical selected execution

The nested `best.execution` is then passed through the existing Step 164 `ModelExecutionResultNormalizer`.

This preserves direct-caller compatibility while ensuring the active orchestration path can never accept a lightweight or malformed execution object from an injected recovery implementation.

### Canonical selected evaluation

The nested `best.evaluation` continues through the Step 170 `ResponseEvaluationResultNormalizer`.

## Compatibility

Step 171 does not change recovery ranking policy, score comparison, candidate order, retry limits, provider invocation behavior, execution budgets, or early-stop behavior.

Existing built-in outcomes remain semantically unchanged:

- passing initial evaluation → recovery unused;
- exhausted budget → recovery unused;
- blocked/unknown provider → no consumed recovery attempt;
- failed attempted provider → used recovery without improvement;
- better alternative → improved recovery.

The public recovery API remains a dictionary.

## Safety invariant

canonical primary execution
→ canonical initial evaluation
→ bounded quality recovery
→ canonical recovery envelope
→ shared-budget/candidate consistency checks
→ canonical selected execution
→ canonical selected evaluation
→ optional replacement
→ outcome memory / final orchestration result.

Quality recovery remains an optimization mechanism. `improved=True` means the existing evaluator selected a higher-scoring alternative; it is not proof of factual truth, superior reasoning, grounding correctness, or calibrated model quality.

## Design boundary

This step validates recovery-result integrity only.

It does not change:

- retrieval;
- evidence normalization;
- provenance;
- freshness;
- conflict detection;
- confidence signals;
- grounding authorization;
- response-evaluation methodology;
- routing policy;
- provider credentials;
- external network behavior;
- RAG;
- embeddings;
- model training; or
- semantic truth inference.

## Regression coverage

`backend/tests/test_step171.py` covers:

1. valid envelope normalization and extension metadata preservation;
2. `used` / candidate consistency;
3. recovery-attempt consistency;
4. improved-best candidate consistency;
5. best model/execution identity consistency;
6. nested evaluation validation;
7. canonical built-in pass-path output;
8. compatibility with legacy direct callers after failed provider recovery;
9. malformed injected envelope rejection;
10. orchestration/shared-budget mismatch rejection;
11. inconsistent improved/model-replacement rejection;
12. rejection of a non-canonical selected execution at the orchestration boundary; and
13. acceptance of a valid injected no-recovery envelope with extension metadata preservation.

## Validation truth

Dedicated Step 171 regression coverage is committed. Repository structure and the final Git diff are verified in this workflow. A targeted pytest run covering Steps 171, 170, 169, 54, and 34 was attempted from a fresh checkout, but the available runtime could not resolve `github.com`; the clone failed before pytest started. No automated test-pass claim is made.
