# Step 145 — Retrieval Provider Reason Contract Hardening

## Objective

Make the optional reason field in the canonical retrieval-provider response contract explicit and stable.

## Problem Found

The response contract already validated that `reason` was a string when present, but it accepted an empty or whitespace-only reason. That creates an ambiguous failure/status record: a response can claim a non-completed state while carrying a reason value that contains no usable information.

Step 141 already applies equivalent validation at the external HTTP adapter boundary. Step 145 brings the same invariant into the canonical provider-response contract so every provider implementation receives the same structural rule.

## Implementation

The canonical `RetrievalProviderResponse` contract now:

- keeps `reason=None` valid because reason remains optional for backward compatibility;
- requires an explicitly supplied reason to be a nonempty string;
- rejects empty and whitespace-only reasons;
- trims surrounding whitespace from valid reasons;
- preserves the existing default reason behavior in retrieval-result normalization when a non-completed response omits a reason.

No new reason values are invented by this step.

## Safety Invariant

`explicit reason present → nonempty canonical reason`

`reason absent → None → downstream normalizer may apply its existing status-specific default`

This step does not decide whether a provider's reason is truthful; it only guarantees that the supplied reason has valid structure.

## Regression Coverage

Dedicated Step 145 tests cover:

1. trimming a valid reason;
2. rejecting an empty reason;
3. rejecting a whitespace-only reason;
4. rejecting a non-string reason;
5. preserving optional omission and existing downstream default behavior;
6. preserving a canonical reason through retrieval-result normalization.

## Scope

Retrieval-provider response reason validation/canonicalization only.

No new network behavior, endpoint, credentials, vendor integration, LLM, RAG, embeddings/vector database, semantic truth verification, ML/DL, or model execution is introduced.

## Validation Truth

Dedicated Step 145 regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
