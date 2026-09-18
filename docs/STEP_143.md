# Step 143 — Retrieval Provider Identity Preservation

## Objective

Preserve the identity of the retrieval provider at the execution boundary, including when provider execution fails before a provider response can supply its own identity.

## Problem Found

The provider executor previously looked only for a `name` attribute. The configured Step 135 HTTP provider exposes its canonical identity as `provider_name`. Therefore, if that provider failed during execution or returned malformed output, the generated retrieval result could lose provider identity even though the executor knew which implementation it had invoked.

This weakens failure provenance and makes retrieval diagnostics less precise.

## Implementation

The executor now resolves provider identity in this order:

1. non-empty `provider_name`;
2. non-empty legacy `name`;
3. `None` when neither is a valid string.

The existing response normalizer still has precedence when a valid provider response explicitly contains its own provider identity. The executor does not invent an identity from a class name, module name, endpoint, or other heuristic.

## Safety Invariant

`provider execution failure → retrieval result preserves the provider's declared identity when available`

No identity is fabricated when the provider exposes no valid identity.

## Scope

Provider identity/provenance preservation at the execution boundary only. No new network behavior, endpoint, credentials, vendor, LLM, RAG, embeddings/vector database, semantic truth verification, ML/DL, or model execution.

## Validation Truth

Dedicated Step 143 regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
