# Step 180 — Developer-Supplied Evidence Reality-State Input

## Objective

Allow developers who already have search, RAG, crawler, database, or connector results to submit source-scoped evidence directly to AI Reality Layer and receive the same deterministic claims, evidence-linking, provenance, observation, freshness, conflict, confidence, and Reality State processing without operating a separate retrieval provider.

## Why this is the correct next step

The initial user hypothesis is an AI application or agent developer who already works with changing information.

The repository could already:

- retrieve through an opt-in HTTPS provider;
- normalize successful evidence;
- extract claims;
- link claims to sources;
- build source provenance;
- observe sources;
- assess freshness;
- detect deterministic conflicts;
- aggregate confidence signals;
- assemble a Reality State.

But the public API still required the Reality Layer itself to own the retrieval step.

That left a major usability gap for developers who already possess retrieved evidence.

Step 180 closes that gap without pretending caller-supplied documents were retrieved by this system.

## New endpoint

Step 180 adds:

`POST /api/v1/reality-state/evidence`

The existing endpoint remains unchanged:

`POST /api/v1/reality-state`

The original route continues to accept only a task and use the configured retrieval path.

The new route accepts a task plus source-scoped documents.

## Request shape

Example:

```json
{
  "task": "What is the current status of Company X?",
  "documents": [
    {
      "title": "Company X official update",
      "uri": "https://example.com/company-x-official",
      "content": "Company X launched Feature A today."
    },
    {
      "title": "Independent report",
      "uri": "https://example.com/company-x-report",
      "content": "not Company X continues to operate."
    }
  ]
}
```

## Bounded input contract

Each document is explicitly source-scoped.

Current bounds:

- 1–20 documents;
- content: 1–50,000 characters per document;
- URI: 1–2,048 characters;
- title: optional, up to 500 characters;
- URI scheme: HTTP or HTTPS;
- source URIs must be unique within one request;
- unexpected fields are rejected.

The task retains the existing 10,000-character upper bound and additionally rejects blank/whitespace-only input.

## Why source-scoped documents matter

The existing retrieval evidence shape contains one combined content field and a list of sources.

If a caller supplied multiple documents as one undifferentiated blob, every extracted claim could incorrectly appear linked to every source.

Step 180 avoids that.

Claims are extracted separately from each submitted document before aggregation.

Therefore:

```
document A
→ claim A
→ source A

document B
→ claim B
→ source B
```

rather than:

```
combined blob
→ every claim
→ every source
```

This makes direct multi-source evidence substantially more trustworthy.

## Duplicate claim handling

If the same exact normalized claim appears in more than one submitted document, Step 180 stores the claim once and merges its source references.

Example:

```
Source A → "Feature A launched."
Source B → "Feature A launched."
```

becomes one claim with two source references.

Claim/evidence linking then creates the corresponding source relationships while keeping the logical claim count deduplicated.

## Conflict detection

Because source lineage is preserved before aggregation, deterministic cross-source conflicts can now be represented correctly.

For example:

```
Source A → "Company X continues to operate."
Source B → "not Company X continues to operate."
```

produces separate claims with separate source references and allows the existing conflict detector to identify the explicit negation pair.

The confidence layer therefore remains uncertain when candidate conflicts are present.

## Direct evidence is not fake retrieval

Step 180 does not wrap caller documents in a synthetic retrieval-provider result and does not mark a network retrieval as executed.

The direct path begins at validated submitted evidence and then invokes the existing downstream Reality Layer components.

This preserves semantic honesty:

```
caller-owned retrieval/search/RAG
            ↓
submitted evidence boundary
            ↓
Reality Layer processing
```

rather than claiming:

```
AI Reality Layer performed retrieval
```

when it did not.

## Canonical downstream processing

The public orchestration function:

`build_reality_state_from_evidence()`

performs:

1. submitted evidence bundle validation;
2. canonical completed-evidence construction;
3. evidence-quality validation;
4. per-source claim extraction;
5. duplicate-claim/source-ref merging;
6. claim/evidence linking;
7. deterministic conflict detection;
8. source provenance construction;
9. source observation;
10. freshness assessment;
11. confidence-signal aggregation;
12. canonical Reality State assembly.

No model execution is involved.

## Freshness semantics

Submitted source documents are observed when they enter the Reality Layer.

Step 180 does not interpret this observation timestamp as the source publication timestamp.

No publication-time/freshness window is supplied by this first direct-evidence contract.

Therefore source freshness remains:

`unknown`

and confidence remains:

`uncertain`

unless another uncertainty signal already dominates.

This is intentional: ingestion time is not proof of information freshness.

## Retrieval independence

The direct-evidence path does not invoke:

- `HttpRetrievalProvider`;
- registry provider selection;
- external retrieval configuration;
- external network access.

A regression test configures an HTTP retrieval endpoint and replaces the provider's `retrieve()` method with a function that fails if called. The direct-evidence Reality State still succeeds.

This proves the boundary is genuinely developer-supplied evidence, not hidden retrieval.

## Existing route compatibility

`RealityStateRequest` remains task-only.

Step 180 does not add `documents` to the existing `POST /api/v1/reality-state` contract.

Developers can therefore choose explicitly:

### Let AI Reality Layer retrieve

`POST /api/v1/reality-state`

### Supply evidence already retrieved elsewhere

`POST /api/v1/reality-state/evidence`

This avoids ambiguous request behavior and preserves Step 134 compatibility.

## Shared HTTP contracts

The new endpoint reuses the existing public API boundaries:

- 200 → `RealityStateResponse`;
- 422 → `ValidationErrorResponse`;
- 500 → `InternalErrorResponse`;
- optional request `X-Request-ID`;
- response `X-Request-ID`.

It appears in OpenAPI with its dedicated `EvidenceRealityStateRequest` schema.

## Security and trust boundary

Submitted content is treated as untrusted evidence input.

The endpoint:

- does not execute submitted content;
- does not fetch submitted source URIs;
- does not treat a URI as proof of source truth;
- does not elevate unknown freshness to support;
- does not run a model over the evidence;
- does not claim semantic verification.

A source URI provides provenance identity, not source trust.

## Design boundary

Step 180 adds developer-supplied evidence ingestion for Reality State construction.

It does not add:

- scraping;
- URL fetching;
- vendor search APIs;
- authentication/authorization;
- database persistence;
- file upload;
- vector databases;
- embeddings;
- semantic claim verification;
- learned confidence calibration;
- model training;
- autonomous agents;
- deployment infrastructure.

## Regression coverage

`backend/tests/test_step180.py` covers:

1. bounded source-scoped request validation;
2. blank task rejection;
3. empty document rejection;
4. unsupported URI-scheme rejection;
5. duplicate source URI rejection;
6. document-count bounds;
7. per-source claim lineage;
8. exact duplicate claim merging across source refs;
9. multi-source Reality State assembly;
10. cross-source deterministic conflict detection;
11. claim/evidence link coverage;
12. provenance/observation/freshness generation;
13. direct-evidence network/retrieval independence;
14. direct HTTP handler behavior;
15. preservation of the original task-only Reality State request;
16. OpenAPI request/response/error/header contracts;
17. canonical `RealityStateResponse` declaration.

## Validation truth

Backend tests run #81 on the initial Step 180 code-bearing regression commit completed successfully with **1194 passed / 0 failed**.

Final Step 180 completion requires the documentation and project-status synchronized repository HEAD to reproduce a fully green GitHub-hosted suite.
