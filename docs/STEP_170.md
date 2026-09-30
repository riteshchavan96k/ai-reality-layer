# Step 170 — Response Evaluation Contract Validation

## Objective

Add a canonical integrity boundary for response-evaluation results before they are consumed by orchestration, quality recovery, execution tracing, and outcome memory.

## Why this is the correct next step

Step 164 established a canonical model-execution outcome. Step 169 then closed the quality-recovery path that could replace that canonical execution with an incomplete recovery dictionary.

The next exposed boundary on the active success path was response evaluation.

Before Step 170:

- `OrchestrationPipeline` accepted an injectable evaluator and trusted its raw dictionary immediately.
- The pipeline read `status` and `score` before any validation.
- Quality recovery used evaluation scores to compare model responses.
- Recovery could return a nested best evaluation that the pipeline trusted directly.
- Outcome memory later persisted the selected evaluation score.

No evaluation contract or normalizer existed in `backend/app/evaluation/`.

A malformed, non-finite, out-of-range, or structurally invalid evaluation could therefore influence recovery, tracing, or persistence without a canonical validation boundary.

## Canonical contract

Step 170 introduces immutable `ResponseEvaluationResult` plus `ResponseEvaluationResultNormalizer`.

The required core contract is intentionally small:

- `score`: finite numeric value in the inclusive range 0 to 1;
- `status`: `pass` or `review`.

This preserves compatibility with the lightweight `{"score": ..., "status": ...}` dictionaries historically used by direct quality-recovery callers.

## Metadata preservation

Evaluation metadata beyond the required core fields is preserved rather than discarded. This keeps the existing public evaluation shape intact, including:

- structural checks;
- passed/total check counts;
- structural score;
- relevance details;
- task;
- limitation text;
- future extension metadata.

Known structural metadata receives additional integrity checks when present.

The contract deliberately does not force a score threshold to correspond to a particular status. Threshold policy remains the responsibility of the evaluator rather than the transport/integrity contract.

## Integration

### Response evaluator

`evaluate_response()` now routes its existing output through the canonical normalizer before returning the same dictionary-shaped API.

### Quality recovery

Direct callers' initial evaluations are normalized before any pass/review decision or score comparison. Existing minimal evaluation dictionaries remain supported.

Candidate evaluations produced during recovery are also normalized before comparison.

### Orchestration pipeline

The injectable evaluator output is normalized before:

- trace emission;
- quality recovery;
- eventual outcome-memory persistence.

The nested `best.evaluation` returned by recovery is normalized before it can replace the active evaluation or provide the final recovery trace score.

## Validation rules

Step 170 rejects:

- missing `score` or `status`;
- boolean, non-numeric, non-finite, negative, or greater-than-one scores;
- evaluation statuses outside `pass` and `review`;
- malformed structural-check mappings;
- negative check counts;
- `passed_checks > total_checks`;
- invalid structural scores;
- non-mapping relevance metadata;
- empty task or limitation strings when those optional fields are supplied.

## Compatibility

Step 170 does not change the response-evaluation algorithm.

The existing evaluator still combines structural integrity and reference-free lexical relevance, and its current `0.8` pass threshold remains unchanged.

Minimal historical recovery evaluations containing only `score` and `status` remain valid.

Unknown/extension evaluation metadata is preserved in dictionary output.

## Safety invariant

canonical model execution → canonical response evaluation → bounded quality recovery → canonical selected evaluation → outcome memory / orchestration result.

An evaluation score is a prototype quality signal. It is not a factual-truth probability, grounding certificate, safety determination, source-authority score, or calibrated model-quality estimate.

## Design boundary

This step validates evaluation-result integrity only. It does not change retrieval, evidence processing, provenance, freshness, conflict detection, confidence signals, grounding authorization, model routing, recovery ranking policy, provider behavior, network access, credentials, RAG, embeddings, model training, or semantic truth inference.

## Regression coverage

`backend/tests/test_step170.py` covers:

1. minimal historical evaluation dictionaries;
2. preservation of extension metadata;
3. invalid/non-finite/out-of-range scores;
4. invalid statuses;
5. structural metadata consistency;
6. canonical output from `evaluate_response()`;
7. direct quality-recovery compatibility;
8. fail-closed validation of injected pipeline evaluators;
9. validation of nested recovery evaluations; and
10. preservation of valid evaluation metadata through the pipeline.

## Validation truth

Dedicated Step 170 regression coverage is committed. Repository structure and the final Git diff are verified in this workflow. Runtime test execution is reported separately and is never inferred merely from committed tests.
