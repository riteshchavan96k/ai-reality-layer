# Step 139 — External Retrieval Provider Capability Declaration

## Objective

Make the configured external retrieval adapter participate in the existing provider capability-selection boundary instead of bypassing it.

## Problem Found

Step 135 registered the configured HTTP retrieval provider directly for live_web and web_or_official_source. The registry therefore knew which implementation to execute, but it had no RetrievalProviderDescriptor for those source types.

Because capability metadata was absent, the selector intentionally preserved legacy compatibility and skipped capability-fit evaluation. That weakened the provider-selection contract for the first real external provider.

## Implementation

When ARL_HTTP_RETRIEVAL_ENDPOINT_TEMPLATE is configured:

- the HTTP provider is registered through RetrievalProviderDescriptor;
- its declared source types are live_web and web_or_official_source;
- its declared temporal scopes are current and unspecified;
- the same provider/capability declaration is used for both supported source types;
- the unconfigured default path remains unchanged and does not acquire external-provider capability metadata.

## Pipeline Boundary

Source Planner → Retrieval Contract → Provider Registry → Provider Descriptor/Capabilities → Capability Evaluator → Provider Selection → External Retrieval

This makes the existing capability gate authoritative for the configured external adapter.

## Regression Coverage

Dedicated Step 139 tests verify configured descriptors, provider identity, both external source types, both temporal scopes, and the unchanged unconfigured path.

## Scope

No new vendor, credentials, secrets, network behavior, LLM, RAG, embeddings/vector database, semantic truth verification, ML/DL, or model execution was added.

## Validation Truth

Dedicated Step 139 regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
