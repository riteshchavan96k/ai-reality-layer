# Step 184 — Bounded Retrieved-Evidence Processing

## Rationale and roadmap grounding

This step addresses an existing safety/quality gap in the MVP retrieval
pipeline. Direct submitted evidence (Steps 180–181) already caps source count
and per-document content, titles and URIs. Configured retrieval (Steps
179, 182–183) did not enforce comparable limits at the provider-neutral
boundary and allowed too many short sentences to expand into an unbounded
number of candidate claims and evidence links. This is a concrete
product-reliability gap, not a new retrieval provider or a new fact-checker.
The original high-level MVP plan did not preassign a distinct Step 184 title.

## Objective

Bound processing of untrusted configured retrieval evidence before it reaches
candidate claim extraction, conflict analysis and claim/evidence graph
construction. Fail conservatively on invalid inputs while preserving original
source attribution and caller-declared observation freshness from Steps
182–183.

## Contract and defaults

Retrieved sources must conform to the same existing basic MVP document
limits already used for submitted evidence:

| Field | Maximum |
| --- | --- |
| Sources per retrieval response | 20 |
| Source-specific content | 50,000 characters per source |
| Original source URI | 2,048 characters |
| Source title | 500 characters |
| Source observed_at | 64 characters (valid ISO-8601 still required) |
| Unique candidate claims from one retrieved response | 2,000 |

Combined content is limited to:

- One or zero sources: up to 50,000 characters.
- Multiple sources: source count × 50,000 plus two separator characters
  between each document.
- Source-scoped documents must still match the exact top-level aggregate
  content, if supplied, under Step 182.

The four canonical source fields used downstream are `uri`, `title`,
`content` and `observed_at`. To preserve the older provider-neutral
contracts, up to four additional **small scalar** legacy fields (such as
`id` or `url`) are tolerated with field names up to 64 characters and
stringified values up to 500 characters. Evidence normalization discards
unused scalar fields; they do not become provenance. Nested, oversized or
numerous extra metadata fields are **rejected**, not forwarded into Reality
State or consuming agents.

The existing HTTPS response byte limit (default 1,000,000 bytes) remains
active. It protects transport response size and complements these
provider-neutral character/graph limits. No additional dependency is needed.

## Fail-closed processing

1. Configured HTTPS responses violating bounds become a `failed`
   `RetrievalProviderResponse` with a stable reason such as
   `too_many_sources`, `source_content_too_large`,
   `source_uri_too_long`, `source_title_too_long`,
   `retrieved_content_too_large`, or
   `unexpected_source_metadata`.
2. The typed and legacy provider-neutral response contract rejects the
   same conditions. `RetrievalProviderExecutor` already converts this
   validation failure to a failed retrieval rather than constructing a
   partially trusted result.
3. Malformed but structurally shaped retrieval results entering the
   evidence normalizer are downgraded to `invalid_evidence` with zero
   sources and zero content. The pipeline does not construct claims from
   partially accepted documents.
4. Even within input/document size limits, an input with more than 2,000
   unique deterministic extracted sentences is a potential claim-graph
   amplification attack. The **retrieved-only** claim extractor returns
   unavailable with reason `retrieved_claim_limit_exceeded`, with **no
   partial claims or links**.
5. Existing unavailable/failed and blocked retrieval statuses still
   propagate through the original conservative Reality State path.

## Compatibility and architecture

- The Step 182 per-source claim lineage and exact duplicate merging are
  unchanged for in-bounds inputs.
- The Step 183 `observed_at` metadata and freshness policy retain their
  meaning. The added 64-character field bound is applied before timestamps
  are parsed at provider-neutral boundaries.
- Valid single-source legacy content, bounded multi-source scoped content,
  and provider-neutral typed/mapping responses remain supported.
- The existing developer-submitted evidence path has its own independent
  document validation and **is not subject** to the retrieval-only
  2,000-claim budget; no direct-evidence behavior is intentionally changed.
- Legacy small scalar source metadata may still pass through the raw
  provider response for backward compatibility, but it is discarded
  during canonical evidence normalization. Nested or excessive extra
  metadata is rejected rather than forwarded downstream.
- The system does not start fetching source URLs or verifying factual truth.

## Files

- `backend/app/reality/retrieval_input_bounds.py`: shared retrieval caps
  and constant-time-or-linear field validation.
- `backend/app/reality/http_retrieval_provider.py`: explicit failed
  provider outcome on bound violations.
- `backend/app/reality/retrieval_provider_response.py`: enforce bounds
  on typed and legacy provider results.
- `backend/app/reality/evidence_normalizer.py`: reject malformed
  provider-neutral retrieval evidence before downstream stages.
- `backend/app/reality/claim_extractor.py`: cap generated candidate
  claims for retrieved evidence.
- `backend/tests/test_step184.py`: positive and negative edge cases,
  exact boundaries, conservative failure propagation, claim limit and
  end-to-end Reality State tests.

## Validation criteria

- All exact limit boundaries pass and above-limit values fail.
- Neither oversized sources nor unexpected nested source metadata reach
  downstream claims or public state.
- Large but otherwise valid 2,001-sentence retrieved content yields no
  partial candidate claims or links.
- Legitimate 2,000-candidate retrieval input is accepted.
- Legacy single-source, Step 182 source scoping, Step 183 observations and
  direct-evidence extraction continue to pass regression tests.
- The complete GitHub Actions backend compilation and pytest suite passes
  at the final synchronized `main` HEAD.

## Non-goals and limitations

This is deterministic input/resource safety. It does not guarantee source
ownership, truth, protection from all large payloads at the network/server
layer, semantic correctness, production-scale load testing, performance
benchmarks, authentication, new providers, deployment or global monitoring.
