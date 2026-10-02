# Step 177 — Backend Test Runtime and Continuous Integration Validation

## Objective

Replace the repeated "regression tests are committed but not executed" gap with a reproducible backend test environment and an automated GitHub Actions workflow that compiles the application and runs the complete backend regression suite.

## Why this is the correct next step

Steps 168–176 added important repository, execution, evaluation, recovery, orchestration, and HTTP contract hardening.

However, each recent step carried the same unresolved validation limitation:

- regression tests existed;
- the available local runtime could not clone the repository because outbound GitHub DNS/network access was unavailable;
- the repository had no GitHub Actions workflow;
- there was no canonical pytest configuration;
- pytest was not declared in a development dependency file.

At this point, adding another micro-contract would have lower quality value than closing the automated-validation gap.

Step 177 therefore establishes the project's first repository-native backend continuous-integration test path.

## Development dependency separation

Step 177 adds:

`backend/requirements-dev.txt`

The development requirements:

1. include the existing production requirements; and
2. add the pytest runtime used by the regression suite.

Pytest remains out of `backend/requirements.txt`.

This preserves the distinction:

```
production runtime dependencies
            +
development/test dependencies
            =
requirements-dev.txt
```

The current test runtime is pinned to:

`pytest==9.0.2`

for reproducible CI behavior.

## Canonical pytest configuration

Step 177 adds a repository-root:

`pytest.ini`

with:

- `backend/tests` as the test root;
- `test_*.py` as the test-file convention;
- repository root on the Python import path;
- `-ra` summary reporting.

This makes the normal developer command simply:

```
python -m pytest
```

rather than requiring each developer or CI job to remember a custom path/import configuration.

## Local validation workflow

The README now documents:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest
```

These commands are intentionally the same dependency/test path used by continuous integration.

## GitHub Actions workflow

Step 177 adds:

`.github/workflows/backend-tests.yml`

The workflow runs on:

- pushes to `main`;
- pull requests targeting `main`;
- manual `workflow_dispatch`.

The workflow uses read-only repository permissions:

```
permissions:
  contents: read
```

It does not use `pull_request_target`, repository secrets, deployment credentials, provider credentials, or write permissions.

## Python/runtime choice

The workflow uses Python 3.13.

This matches the modern Python runtime already used during repository validation work and supports the project's current dependency set.

The dependency cache keys include both:

- `backend/requirements.txt`;
- `backend/requirements-dev.txt`.

## Validation stages

The CI job performs four high-level operations:

1. check out the repository;
2. install the declared development environment;
3. compile all Python application modules with `compileall`;
4. execute the complete pytest suite.

The compile step runs before pytest so syntax/importable-source problems are surfaced separately from behavioral test failures.

The test command is the complete suite:

```
python -m pytest
```

The workflow does not run only the latest step tests.

## Bounded execution

The test job has a 20-minute timeout.

Concurrency cancellation is enabled for superseded runs on the same workflow/ref, preventing obsolete commits from consuming CI capacity after a newer commit is pushed.

## Security boundary

The workflow intentionally avoids privileged CI patterns.

It has:

- read-only contents permission;
- no secrets;
- no external-provider credentials;
- no `pull_request_target`;
- no deployment operation;
- no write-back to the repository.

A pull-request test run therefore validates code without granting that code repository write authority through this workflow.

## What this step does not do

Step 177 does not configure branch protection or repository rulesets.

The workflow creates a reliable status check, but whether GitHub requires that check before merging is a repository-administration policy separate from the code change.

Step 177 also does not add:

- deployment;
- packaging/publishing;
- Docker images;
- production secrets;
- external-provider integration tests;
- live network retrieval tests;
- load/performance testing;
- authentication/authorization;
- model training.

## Regression coverage

`backend/tests/test_step177.py` verifies the repository's validation infrastructure itself:

1. development requirements inherit production requirements;
2. pytest is pinned in development dependencies;
3. pytest remains absent from production dependencies;
4. pytest configuration points at the complete backend suite;
5. CI runs on push, pull request, and manual dispatch;
6. `pull_request_target` and secret usage are absent;
7. repository permissions are read-only;
8. Python 3.13 and declared development dependencies are used;
9. application compilation occurs before pytest;
10. CI runs the full suite rather than selected step tests;
11. workflow execution is timeout-bounded and concurrency-controlled; and
12. README local validation commands match the CI environment.

## Safety invariant

repository change
→ declared development environment
→ read-only CI checkout
→ application compile validation
→ complete backend pytest suite
→ GitHub Actions result.

A green CI run demonstrates that the declared automated test suite passed in that GitHub Actions environment. It does not by itself prove production correctness, security, factual truth, external-provider availability, or real-world user value.

## Validation truth

Step 177 implementation and self-checking regression coverage are committed. The first GitHub Actions execution result is inspected separately before project-status synchronization; no green-CI claim is made unless GitHub reports a successful completed run.
