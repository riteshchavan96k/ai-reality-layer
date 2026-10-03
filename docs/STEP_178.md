# Step 178 — Full Regression Baseline Reconciliation

## Objective

Restore a truthful green full-repository backend regression baseline after Step 177 made the complete historical test suite executable for the first time.

Step 177 intentionally exposed the repository's accumulated contract/test drift instead of hiding it. Its final baseline was:

- 1074 passed;
- 92 failed.

Step 178 reconciles those failures while preserving the stronger contracts introduced by later steps.

## Selection rationale

Step 177 explicitly identified a green full-repository regression baseline as a separate remediation milestone.

That made regression reconciliation higher priority than adding another feature or contract. Continuing feature work while 92 existing regressions were visible would reduce confidence in every later change.

## Reconciliation rules

Step 178 followed four rules:

1. current production defects were fixed in production code;
2. documented backward-compatibility guarantees were restored where later refactors accidentally broke them;
3. historical tests were updated only when later canonical contracts deliberately superseded the behavior they asserted;
4. no failing test was skipped, xfailed, deleted, or excluded to manufacture a green CI result.

The GitHub Actions workflow still runs the complete backend suite with:

`python -m pytest`

## Production defects repaired

### Evidence consumption integration

`EvidenceNormalizationConsumer` returns the typed `EvidenceNormalizationConsumptionResult`, while the Step 153 normalizer had stopped accepting that producer result.

The normalizer now accepts the typed producer result and converts it into the canonical consumption contract.

### Claim-evidence linking factories

The production linker called:

- `usable_result()`;
- `empty_result()`;
- `unavailable_result()`.

Those canonical factories were missing from `ClaimEvidenceLinkingResult`.

They are restored, together with the derived read-only `unlinked_claim_count` property already represented by serialization.

### Deterministic claim splitting

The sentence-splitting expression was accidentally double escaped, preventing normal whitespace/newline splitting.

The intended deterministic sentence split is restored.

### Grounding consumption integration

The pipeline serialized the grounding contract into state, then later needed a typed contract at the grounding-consumption boundary.

The stored mapping is now normalized back into the canonical typed grounding context before consumption.

### Legacy grounding mapping compatibility

Step 93 documented `grounding_executed=True` as the compatibility default for legacy mappings, but the later strict normalizer had lost that default.

The documented default is restored.

### Unsupported evidence status handling

The evidence consumer's unsupported-status fallback attempted to construct a consumption result with a status the result contract itself forbids.

Unsupported evidence now fails closed through the canonical `unknown` evidence status while preserving the `unsupported_evidence_status` reason.

### Canonical completed evidence → ready grounding

The current evidence normalization pipeline produces `status="completed"`, while the grounding builder still recognized only the older `usable` alias.

The builder now accepts canonical completed evidence as usable grounding input while retaining the historical alias.

### Legacy model-adapter invocation

Fallback execution and quality recovery had started calling every adapter as:

`generate(task, context=context)`

This broke adapters implementing the original supported `generate(task)` signature.

Both paths now use signature-aware invocation:

- adapters accepting `context` receive it;
- legacy task-only adapters continue to execute;
- adapter-raised errors are not hidden behind a broad TypeError retry.

### Mock model grounding metadata

The canonical execution context exposes `grounding_status`, while the mock model still read the obsolete `status` key.

The mock model now reads `grounding_status` and retains the old key only as a compatibility fallback.

## Historical regression reconciliation

Tests predating later contracts were updated to use the current documented boundaries rather than weakening production validation.

The main reconciliations included:

- canonical grounding decision/result classes from Steps 104, 107, 113, and 120;
- canonical Step 123 result import;
- current source-count invariant ordering in Steps 127–128;
- OpenAPI request-schema assertions instead of removed FastAPI private `ModelField.type_` internals;
- public retrieval-result validation rather than a removed private builder;
- canonical provider-selection results;
- typed retrieval provider requests;
- canonical not-required retrieval requests;
- capability-evaluation result objects instead of boolean assumptions;
- full retrieval-result envelopes at the Step 150 consumption boundary;
- required Step 151 consumption fields;
- canonical provider-neutral `blocked` retrieval status;
- provider execution result metadata;
- expanded orchestration traces while preserving legacy core-stage order;
- current outcome-memory and grounded-result fixtures;
- Steps 56–59 dependency injection tests rebuilt on the current default dependency graph with targeted wrapped overrides.

## Dependency-injection test strategy

The modern `OrchestrationDependencies` graph contains many more services than it did at Steps 56–59.

The old tests manually constructed partial dependency containers or used a class spec that no longer exposed all runtime fields.

The reconciled tests now:

1. build `OrchestrationDependencies.default()`;
2. use `dataclasses.replace()` for only the services under observation;
3. wrap real services with mocks when call assertions are needed;
4. allow all later canonical pipeline stages to execute normally.

This continues to test dependency injection without freezing the pipeline at its Step 56-era shape.

## CI progression

Hosted GitHub Actions provided evidence after each repair cluster.

The regression baseline moved through:

- Step 177 final baseline: **1074 passed / 92 failed**;
- early active-path repairs: 1086 passed / 80 failed;
- grounding integration repair: 1102 passed / 64 failed;
- canonical-result/framework reconciliation: 1112 passed / 54 failed;
- retrieval-contract reconciliation: 1141 passed / 25 failed;
- provider/execution and compatibility reconciliation: 1157 passed / 9 failed;
- modernized dependency tests: 1160 passed / 6 failed;
- completed canonical execution fixtures: **1166 passed / 0 failed**.

No failure count was reduced by test exclusion.

## Step 178 regression coverage

`backend/tests/test_step178.py` locks in the highest-risk production repairs:

1. typed evidence-consumption result integration;
2. claim-linking factories and derived unlinked count;
3. deterministic sentence splitting/deduplication;
4. legacy grounding-execution default;
5. canonical completed evidence reaching ready grounding;
6. unsupported evidence failing closed as canonical unknown;
7. mock model use of canonical `grounding_status`;
8. legacy `generate(task)` fallback support;
9. legacy `generate(task)` quality-recovery support.

## Safety invariant

historical + current regression suite
→ classify actual production defect vs superseded test expectation
→ fix the owning boundary
→ preserve canonical validation strength
→ execute the complete suite
→ zero failures before completion.

A green unit/regression suite is evidence that the repository's declared automated contracts are mutually consistent. It is not proof of factual truth, production security, live-provider availability, scalability, or real-world product-market fit.

## Design boundary

Step 178 is regression-baseline reconciliation.

It does not add:

- new model providers;
- new retrieval vendors;
- external credentials;
- deployment infrastructure;
- RAG/vector databases;
- embeddings;
- model training;
- autonomous agents;
- new product UI;
- semantic truth claims.

## Validation truth

Step 178 reached a real GitHub-hosted green full-repository regression baseline.

The first code checkpoint that eliminated the Step 177 baseline debt was Backend tests run #59 (`37104958968`) at commit `6f7337af29d5e68285e93dd5d66edc6d3ed0bb37`, with **1166 passed / 0 failed**.

Step 178 then added dedicated reconciliation regressions and one final canonical completed-evidence claim-extraction repair. Backend tests run #62 (`37105127807`) on commit `33e6735782e33dabef900f16363bee05ef241e1a` completed successfully with:

- checkout: passed;
- Python 3.13 setup: passed;
- development dependency installation: passed;
- backend compile validation: passed;
- complete pytest suite: **1175 passed**;
- failures: **0**;
- Step 178 regression tests: passed.

No test is skipped, xfailed, deleted, or excluded to produce the green result. The workflow continues to execute the complete backend suite with `python -m pytest`.

The final project-status synchronization is validated by a separate GitHub Actions run before Step 178 is marked complete.
