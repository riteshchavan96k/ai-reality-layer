# Step 212 — Canonical Source-URI Identity Integrity

## Verified gap

On the verified Step 211 `main` implementation, source identity was
inconsistent when a retrieval provider returned a valid URL with leading or
trailing whitespace:

- `HttpRetrievalProvider` validated a URI but retained its untrimmed value
  and compared duplicate source URLs without normalization.
- `RetrievalEvidenceNormalizer` retained untrimmed URI strings and used
  raw string equality for its duplicate check.
- `EvidenceClaimExtractor` accepted different padded spellings of the
  same URI as distinct sources, and included raw source references in claims
  and calls to optional semantic adapters.
- `SourceProvenanceBuilder` hashed the raw URI, creating a different
  source ID for each whitespace alias.
- `ClaimEvidenceLinker` already trimmed source references. Thus links
  could refer to a trimmed identifier that did **not** equal the source
  reference in the provenance record.
- `SourceObservationBuilder` matched retrieval records using raw URI
  strings. After source identity normalization, direct builder callers also
  needed to match the same canonical values and reject collisions.

This is a real claim-to-source traceability defect, not a cosmetic
normalization or reason to add another product subsystem.

## Objective and boundary

Make URI *identity* consistent throughout the existing retrieval,
claim-extraction, provenance, observation and linking pipeline, without
inventing sources or rewriting the meaning of URLs.

**Canonical rule:** Remove only leading and trailing whitespace via
Python `str.strip()`. Keep the remainder of the URL byte-for-byte at the
Unicode string level. No lowercasing, slash rewriting, case folding,
query parameter sorting, percent decoding, redirect following, or invented
publisher identity.

Canonicalization must occur **before** duplicate detection and hashing.

## Implementation

### HTTP retrieval ingress

`backend/app/reality/http_retrieval_provider.py` trims each validated
URI and retains that trimmed representation in the provider response.
Existing HTTP(S) validation and source-count, metadata, body-size, and
source-content checks remain. Padded aliases such as `uri` and
`"  " + uri + " "` now trigger the existing `duplicate_source_uri`
failure rather than becoming separate purported sources.

### Provider-neutral normalization

`backend/app/reality/evidence_normalizer.py` trims retrieved source URI
strings in the canonical evidence representation; existing conversion
of non-string legacy fields remains as before. Its existing duplicate
source detection now compares canonical URI strings, yielding
`invalid_evidence` on whitespace aliases without creating candidate
claims from a contradictory source set.

### Low-level extraction

`backend/app/reality/claim_extractor.py` trims verified source URI
strings **before** duplicate attribution validation and uses those
canonical source references for both source-scoped and historical
single-source evidence. Empty and non-string URIs still produce the
existing `missing_source_attribution` result.

Duplicate canonical URIs produce the existing
`duplicate_source_attribution` result with no claims or semantic adapter
calls. Valid candidate claim text, global deduplication, semantic
structuring limits, and optional adapter call budgets are unchanged.

### Provenance and temporal observation

`backend/app/reality/source_provenance_builder.py` uses canonical
trimmed source URIs for `uri`, `source_ref`, deduplication and the
existing SHA-256 URI identity. This ensures a padded spelling cannot
create a second source identity or split the provenance hash.

`backend/app/reality/source_observation_builder.py` matches direct
retrieval input source records to provenance URIs on canonical trimmed
keys and retains the existing fail-closed
`retrieval_source_provenance_mismatch` outcome when aliases collide.
The source-reported observation timestamp is not invented or changed.

The existing `ClaimEvidenceLinker` already trims source references, so
with normalized upstream references its links now agree with provenance
identifiers. No separate new linker class or contract is introduced.

### Submitted evidence compatibility

`SubmittedEvidenceDocument` already trims source URIs before building
a source-scoped evidence bundle. That input continues working without
changes to its API contract, maximum 20 documents, content size limit,
or unique URI constraint.

## Validation cases

`backend/tests/test_step212.py` covers:

- HTTP ingress canonicalization and duplicate padded aliases;
- provider-neutral evidence normalization and fail-closed duplicates;
- `usable` and `completed` low-level claim extraction;
- legacy single-source extraction, rejected ambiguous source aliases,
  and zero optional semantic adapter calls on rejection;
- deduplicated cross-source attribution given to an injected adapter;
- stable SHA-256 source IDs and low-level provenance deduplication;
- cross-check of claim links and provenance references;
- retrieval-observation matching with padded URI input and safe failure
  on duplicate normalized keys;
- distinct URL meanings preserved (for example, slash suffix);
- submitted-evidence compatibility;
- an end-to-end configured HTTP retrieval to Reality State, asserting
  identical canonical identities across evidence, claims, source
  provenance, claim links, and observations.

The complete historical test suite must pass, including Steps
157, 180–185, 206–211.

## Security and honesty

The improvement addresses lexical source identity, **not** proof of
publisher authenticity, domain ownership, factual reliability, or URL
safety. A source reference is only a reported pointer to evidence.
URLs differing in significant characters are not silently merged.
No network requests are made to source URLs as part of normalization.

This step does not add a model, ML, DL, Hugging Face, LLM, a new data
store, entity resolution, or changes to conflict and confidence logic.
It keeps the existing architecture and API shapes intact.

## Completion criteria

Only mark Step 212 complete after GitHub-hosted Python 3.13 compilation
and the entire pytest suite pass on the PR head, after the PR is merged
and separately verified on `main`, and after the final status update
passes on its exact `main` commit SHA.
