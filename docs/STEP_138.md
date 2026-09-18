# Step 138 — External Retrieval Source Provenance Validation

## Objective

Prevent malformed external retrieval payloads from entering the provider-response contract with unusable source provenance.

## Problem Found

Step 135 normalized external JSON source objects structurally, but it allowed arbitrary `uri` and `title` values to pass through. Downstream evidence-quality validation could later reject invalid provenance, but the external provider boundary itself was too permissive.

## Implementation

- Validate every supplied source URI when present.
- Permit only HTTP(S) source URIs with a valid network location.
- Reject empty or non-string source URIs.
- Validate optional source titles as strings.
- Reject sources that contain neither URI nor title.
- Preserve arbitrary additional source metadata rather than deleting it.
- Preserve the existing fallback source URI when content is returned without sources.
- Continue failing closed with a failed provider response rather than treating malformed payloads as evidence.

## Pipeline Boundary

`External JSON → HttpRetrievalProvider → RetrievalProviderResponse → RetrievalResult → Evidence Quality`

This hardens the external trust boundary. It does not establish that a source is truthful, authoritative, current, or relevant.

## Regression Coverage

Dedicated Step 138 tests cover invalid URI, invalid title, missing provenance, and valid HTTP/HTTPS sources.

## Scope

No vendor integration, credentials, secrets, LLM, RAG, embeddings, vector database, semantic truth verification, ML/DL, or new network behavior was introduced.

## Validation Truth

Dedicated Step 138 regression tests are committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.