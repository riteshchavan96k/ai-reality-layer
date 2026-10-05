# Step 182 — Source-Scoped Retrieval Claim Lineage and Provenance Integrity

## Objective

Ensure the configured retrieval → Reality State path only attributes a candidate claim to the original source document(s) actually containing it, while conservatively rejecting ambiguous or unverifiable source attribution.

## Why Step 182 follows Steps 179–181

- Step 179 restored the working configured HTTPS retrieval → Reality State pipeline.
- Step 180 introduced source-scoped claim attribution for *submitted* evidence.
- Step 181 added explicit observation-age freshness for submitted evidence.

The configured retrieval path still used one combined content body with a list of sources. Its deterministic claim extractor assigned the *entire list of source URIs* to every sentence, regardless of which source contained that sentence. The configured HTTP adapter also substituted the retrieval gateway URL when a successful response had content but no sources.

Both behaviors can mislead downstream agents about claim provenance. Accurate claims → evidence → source relationships take priority over additional integrations.

## Source-scoped provider input

Providers can return original source documents in the existing source list:

    {
      "status": "completed",
      "sources": [
        {
          "uri": "https://example.test/official",
          "title": "Official update",
          "content": "Company X launched Feature A. Shared claim."
        },
        {
          "uri": "https://example.test/report",
          "title": "Independent report",
          "content": "Company X hired 20 staff. Shared claim."
        }
      ]
    }

For scoped responses:
- each source needs a unique original HTTP(S) source URI;
- every source must contain a nonblank string content field;
- when a top-level combined content field is supplied, it must equal the ordered, blank-line-separated source content, after each document is stripped;
- without top-level content, the content is assembled deterministically from source documents;
- scoped content remains attached to each source through evidence normalization.

URIs are attribution identifiers, not proof of source ownership, truth, or independent verification. No URI fetching is performed by this step.

## Claim attribution

Claims are extracted separately from each source document.

Unique claims retain *only that source's URI*. Exact normalized duplicate claims retain all actual contributing URI references in first-observed order.

For example:
- Official source only: Company X launched Feature A. → official URI.
- Independent report only: Company X hired 20 staff. → report URI.
- Text repeated by both documents → both URIs.

The existing claim/evidence linker, provenance builder, observation builder, freshness evaluator, conflict detector, confidence aggregator and Reality State assembler are reused.

## Fail-closed behavior

1. Multi-source combined content without source-scoped text: claim extraction is unavailable, reason ambiguous_source_attribution. No claims or links are invented.
2. No original URI: the HTTP adapter never synthesizes an original source URI from its own retrieval gateway. Source-less content produces no attributed claims.
3. Title-only completed HTTP source: fails with source_uri_required.
4. Duplicate source URIs: rejected.
5. Partial, blank, non-string, or contradictory per-source content: HTTP responses fail; malformed provider-neutral evidence is rejected by canonical evidence normalization.
6. Valid legacy single-source combined text: unchanged, since exactly one genuine URI identifies its source.

Failing to establish a source is not proof that its text is false. It prevents an unsupported provenance claim.

## Architecture

    Configured HTTPS retrieval
      → provider response / provider-neutral retrieval result
      → evidence normalization retains each source's content
      → per-source claim extraction and exact duplicate merge
      → canonical claim/evidence links
      → source provenance / observations / freshness
      → conflict detection / conservative confidence
      → Reality State

The first three boundaries change; this is not a new provider or a parallel pipeline.

## Compatibility and design boundary

- Legacy single-source retrieval payloads continue to work.
- Multi-source combined payloads remain representable but cannot claim unsupported per-source provenance.
- The developer-supplied evidence API from Steps 180–181 is untouched.
- The explicit source freshness policy remains unchanged and does not certify publication age, truth, or ownership.
- No new network access, vendor-specific provider, credentials, ML, training, embeddings, persistence, authentication, deployment, or autonomous agents.

## Regression coverage

The dedicated backend/tests/test_step182.py tests validate the HTTP format, the provider-neutral evidence normalization, source-specific claims, duplicate source refs, missing and ambiguous attribution, malformed documents, backward compatibility, and full end-to-end Reality State provenance and conflict lineage.

The historical Step 125 test that assigned every URI to an unattributed claim, and the Step 135 test that expected a synthesized gateway source URI, are reconciled with the stronger provenance rules. Neither regression is skipped or deleted.

## Completion bar

The entire backend suite must pass on the final synchronized GitHub HEAD. A green suite demonstrates the tested structural behavior, not semantic truth verification or external source authenticity.
