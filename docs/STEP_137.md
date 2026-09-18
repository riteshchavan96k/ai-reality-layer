# Step 137 — Current Information Retrieval Integration

## Objective

Ensure tasks classified as requiring current information actually cross the retrieval boundary.

## Problem Found

The source planner correctly selected `live_web` when `needs_current_info` was true, but its `requires_retrieval` flag depended only on `needs_external_evidence`. As a result, current-information requests could be planned for live web while still producing a `not_required` retrieval contract.

That prevented the Step 135 external retrieval provider from being reached for the current-information path.

## Implementation

- `requires_retrieval` is now true when either current information or external evidence is required.
- Existing source-type and priority selection remains unchanged.
- General-knowledge tasks continue to avoid retrieval.
- Current-information requests take the existing `live_web` path.
- External-evidence requests continue to use `web_or_official_source`.

## Pipeline Boundary

`Reality Context → Source Planner → Retrieval Contract → Provider Selection → External Retrieval`

This step fixes orchestration reachability. It does not add a new retrieval provider.

## Regression Coverage

Step 137 tests cover current-information retrieval, external-evidence retrieval, general knowledge, and the combined-flags case.

## Scope

No LLM, RAG, embeddings, vector database, ML/DL, semantic truth inference, vendor lock-in, credentials, or new network behavior was introduced.

## Validation Truth

Dedicated Step 137 regression tests are committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.