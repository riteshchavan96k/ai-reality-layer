# Step 141 — External Retrieval Response Status Integrity

## Objective

Preserve the provider status and reason returned by the configured external retrieval endpoint instead of assuming every structurally valid JSON payload represents successful retrieval.

## Problem Found

The Step 135 HTTP adapter accepted a valid JSON object and then always constructed a `completed` provider response. That meant an upstream payload explicitly reporting `failed` or `blocked` could be incorrectly converted into successful retrieval.

## Implementation

The adapter now:

- accepts only the existing provider response statuses;
- preserves `failed`, `blocked`, and `provider_unavailable` statuses;
- preserves a valid upstream reason;
- rejects unsupported provider statuses;
- rejects malformed non-string reasons;
- keeps the existing successful-response normalization and source-provenance validation unchanged.

## Safety Invariant

`external status != completed → provider response is not converted to completed`

This is contract integrity, not factual truth verification.

## Scope

No new network behavior, endpoint, credentials, vendor, LLM, RAG, embeddings/vector database, semantic truth verification, ML/DL, or model execution was added.

## Validation Truth

Dedicated Step 141 regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
