# Step 144 — Retrieval Provider Identity Contract Hardening

## Objective

Make provider identity in the canonical retrieval-provider response contract explicit and stable before the response is converted into the provider-neutral retrieval result.

## Problem Found

Step 143 preserved provider identity at the execution boundary by resolving a provider's declared `provider_name` or legacy `name`. However, the canonical `RetrievalProviderResponse` contract still accepted an explicitly supplied empty or whitespace-only provider identity.

That created an avoidable contract ambiguity: a response could carry a provider field that was present but not a valid identity. Downstream code should not have to interpret whitespace as an identity.

## Implementation

The canonical response contract now:

- accepts `provider=None` when the provider response does not declare an identity, allowing the executor's Step 143 fallback to supply the implementation identity;
- requires an explicitly supplied provider identity to be a nonempty string;
- trims surrounding whitespace from valid provider identities before the response is exposed downstream;
- rejects non-string provider identities;
- preserves the existing precedence rule in `RetrievalResultNormalizer`: an explicit response identity is used when present, otherwise the executor-provided fallback identity is used.

This is contract validation and canonicalization only. It does not infer an identity from a class name, module name, endpoint, URL, or other heuristic.

## Safety Invariant

`explicit provider identity present → nonempty canonical provider identity`

`provider identity absent → None, allowing the execution boundary to provide a declared fallback`

No provider identity is fabricated.

## Regression Coverage

Dedicated Step 144 tests cover:

1. trimming a valid provider identity;
2. rejecting empty identities;
3. rejecting whitespace-only identities;
4. rejecting non-string identities;
5. preserving executor fallback when response identity is absent;
6. preserving explicit response identity over the fallback.

## Scope

Retrieval-provider response identity contract hardening only.

No new network behavior, endpoint, credentials, vendor integration, LLM, RAG, embeddings/vector database, semantic truth verification, ML/DL, or model execution is introduced.

## Validation Truth

Dedicated Step 144 regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
