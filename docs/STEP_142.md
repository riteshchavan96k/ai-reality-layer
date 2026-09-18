# Step 142 — Retrieval Provider Response Payload Consistency

## Objective

Make the canonical retrieval-provider response contract internally consistent: a response that did not complete successfully must not carry successful-retrieval payload data such as sources or content.

## Problem Found

Step 141 correctly preserved upstream provider statuses. The canonical response contract still allowed a non-completed response to carry `sources` or `content`. That creates an ambiguous state: downstream code could see a failed or blocked status alongside data that looks like successful retrieval.

## Implementation

The canonical `RetrievalProviderResponse` contract now rejects:

- non-`completed` responses containing sources;
- non-`completed` responses containing content.

The external HTTP adapter also validates this boundary before constructing a non-completed response. If an upstream failed/blocked/provider-unavailable payload includes retrieval data, the adapter fails closed with:

`invalid_non_completed_payload`

A valid non-completed response may still carry its explicit status and optional reason, but it contains no retrieval content or sources.

Completed responses retain their existing content and source behavior.

## Safety Invariant

`status != completed → sources == empty AND content == None`

This prevents status/data ambiguity. It does not establish factual truth, source authority, freshness, or semantic correctness.

## Scope

No new network behavior, endpoint, credentials, vendor, LLM, RAG, embeddings/vector database, semantic truth verification, ML/DL, or model execution was added.

## Validation Truth

Dedicated Step 142 regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
