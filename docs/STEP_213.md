# Step 213 — Canonical Source-Provenance Identity Coherence

## Verified gap after Step 212

Step 212 normalized source URIs at retrieval and evidence ingestion. It
aligned claim references, evidence links, source provenance hashes and
observations produced through the normal pipeline. Inspection of the
canonical `SourceProvenance` and `SourceProvenanceResult` types
revealed an open validation gap for **directly constructed and
mapping-deserialized provenance**.

Before Step 213:

1. `SourceProvenance` required nonempty `source_ref` and `uri`, but did
   not require them to agree. A record could say that the same source
   both was `https://example.test/a` (URI) and supported a claim from
   `https://example.test/b` (reference). This breaks Step 212 identity.
2. Direct provenance records could retain surrounding URI whitespace even
   though the Step 212 builder's output was canonical.
3. `SourceProvenanceResult` checked `source_count` against the number
   of records but did not require `source_id` and `source_ref` to be
   unique. Two purportedly independent records could represent the
   same URI or use the same ID for different URIs. Downstream observation
   and freshness work is keyed by source IDs, and claim linking uses
   source references; ambiguity matters.

The normal `SourceProvenanceBuilder` already emits coherent records, so
we must preserve it rather than create a new subsystem.

## Objective

Enforce unambiguous canonical source identity at the existing typed and
mapping-shaped provenance contracts, including callers that bypass the
builder, **without breaking older valid source IDs used by legacy tests**.

## Implementation

Changed only `backend/app/reality/source_provenance.py` in production.

### Single-record integrity

`SourceProvenance.__post_init__` now requires:

- `uri` is already stripped of surrounding whitespace;
- `source_ref == uri`;
- existing nonempty string, title-type and
  `identity_method="sha256_uri"` checks remain.

An invalid record raises a clear `ValueError`, rather than being
retained as a potentially trusted canonical provenance record.

`SourceProvenanceResult.validate(mapping)` creates typed
`SourceProvenance` records, so these checks also apply to
mapping-deserialized input. The normalizer uses the same validator.

### Multi-record identity uniqueness

`SourceProvenanceResult.__post_init__` rejects:

- duplicate `source_id` values in its source tuple;
- duplicate `source_ref` values in its source tuple.

The prior `source_count == len(sources)` invariant remains.

This catches ambiguous identity even when an external producer claims
two records were processed. It prevents duplicate provenance identities
from silently propagating into source-observation construction.

### Explicit backward compatibility

- Production `SourceProvenanceBuilder` already trims URI input, merges
  duplicate canonical URIs and hashes the resulting URI string. Its
  normal `sha256_uri` source IDs are preserved.
- Existing direct typed test fixtures with illustrative identifiers
  such as `source-1` remain accepted when their source references and
  URIs are coherent and identities unique.
- This step does **not** introduce a new source-ID format or validate
  the literal hash against the claimed URI. The identity-method label
  remains a structural contract; the production builder continues
  computing actual SHA-256 hashes.
- Empty and unavailable result contracts are unchanged.
- No public API field, output serialization shape, model, database,
  network request, freshness algorithm, claim linking algorithm, or
  confidence policy is changed.

## Validation

`backend/tests/test_step213.py` covers:

- normal builder output with stable SHA-256 identities;
- typed and mapping-shaped mismatched URI/reference rejection;
- padded URI and padded reference rejection;
- duplicate source IDs with distinct source URIs;
- duplicate source references with distinct source IDs;
- mapping and normalizer duplicate rejection;
- correct round trips for two distinct sources;
- legacy non-hash fixture ID compatibility;
- builder deduplication before producing a canonical result;
- downstream observation construction rejecting ambiguous provenance;
- successful observations for valid distinct source IDs;
- valid empty/unavailable result states;
- claim-link/provenance cross-reference agreement after canonical URI trim;
- real developer-submitted Reality State retaining two distinct sources,
  claim references, links, and observation records.

Full Python 3.13 compile and complete pytest regression suite required,
particularly Steps 157–159, 180–195 and 206–212.

## Scope and non-goals

This is a canonical **structural identity** guarantee, not verification
that a source URL is authentic, credible, independent, or actually
supports the content. It does not perform web retrieval of the URL or
certify factual truth.

No new AI/ML/LLM/Hugging Face integration, entity resolution, graph
database, model accuracy claim, or additional validation layer.

## Completion

Mark complete only once feature-branch CI passes, the PR merges,
independent merged-main CI passes, and final status-sync CI passes on
its exact main commit SHA.
