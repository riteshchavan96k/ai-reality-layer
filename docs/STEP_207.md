# Step 207 — Semantic Claim Structuring Execution Boundary

## Verified reason for this step

Step 206 added the canonical `ClaimSemanticStructure` contract but the live
`EvidenceClaimExtractor` had no provider-neutral way to invoke a future
semantic structurer. It always emitted the safe `unstructured` default.

The immediate gap is the execution boundary **between** extracted candidate
sentences and the Step-206 semantic contract, not a missing machine-learning
model. Adding brittle regex triples or pretending an LLM is active would
violate the project's no-fake-intelligence principle.

## Objective

Introduce a small optional semantic structuring stage that:

1. Defaults to an honest `not_attempted` result with no model execution.
2. Accepts a trusted injected structurer without binding to any model provider.
3. Normalizes and validates all returned semantic structure through Step 206.
4. Fails closed to explicit unstructured metadata on invalid output or failure.
5. Preserves claim text, extraction method, and complete source lineage.
6. Works in the existing retrieved-evidence and submitted-evidence paths.
7. Does not alter existing default API response semantics.

## Implementation

### Provider-neutral protocol

`backend/app/reality/claim_semantic_structurer.py` defines:

- `ClaimSemanticStructurer`: a trusted adapter with
  `structure(claim_text, source_refs)`;
- `NotAttemptedClaimSemanticStructurer`: an explicit default returning
  `ClaimSemanticStructure.unstructured()`;
- `ClaimSemanticStructuringStage`: the normalization, validation, and
  error-isolation boundary.

The optional adapter may return a `ClaimSemanticStructure`, a mapping with
the complete canonical Step-206 fields, or `None`.

The stage validates only the **shape and internal consistency** of proposed
semantic data. A schema-valid triple does not prove the triple accurately
represents the sentence, and certainly does not prove factual truth.

### Failure states

| Adapter behavior | Canonical result |
| --- | --- |
| Default not-attempted adapter | `unstructured` / `semantic_structuring_not_attempted` |
| Valid structured output | `structured` with normalized subject/predicate/object/method |
| Explicit valid unstructured output | `unstructured` with adapter's reason |
| No result (`None`) | `unstructured` / `semantic_structuring_no_result` |
| Invalid output or raised exception | `unstructured` / `semantic_structuring_failed` |

No adapter errors, exception messages, or internals are exposed as semantic facts.
Configuration errors (missing callable `structure`) are rejected early.

### Claim extractor integration

`EvidenceClaimExtractor` now accepts an optional `semantic_structurer`
constructor argument. Its historical zero-argument construction remains valid.

Candidate extraction and duplicate merging run **before** semantic structuring.
This means the adapter receives one invocation per unique candidate claim and
the complete source reference tuple (including merged duplicate sources).

The extractor attaches the validated semantic structure to a new canonical
`EvidenceClaim`, preserving the original claim text, extraction method, and
source references.

Unusable evidence, empty evidence, or evidence without valid attribution
does not invoke a structurer.

### Orchestration integration

Both existing Reality State construction paths use the same injected
`services.claim_extractor`. The optional implementation can be supplied
through the existing `OrchestrationDependencies` composition boundary
without adding a new public API field, environment variable, or service.

No external provider is configured by default, and callers **cannot**
request arbitrary model execution by sending data in an API request.

## Regression coverage

`backend/tests/test_step207.py` exercises:

- default no-attempt behavior and legacy claim output;
- typed and mapping-shaped structured results;
- explicit adapter abstention;
- missing and malformed adapter results;
- exception isolation and mixed-success multi-claim behavior;
- deduplication before structuring and complete source lineage;
- no adapter invocation on unavailable/unattributed evidence;
- invalid adapter configuration and stage inputs;
- real submitted-evidence orchestration with injected stage;
- ordinary submitted-evidence output unchanged by default.

The complete historical regression suite must pass, especially the Step-206
semantic contract and extraction/linking compatibility tests.

## Non-goals and safety boundaries

Step 207 does **not** introduce:

- Hugging Face models, NER, LLMs, embeddings, ML/DL inference or network calls;
- heuristic subject/predicate/object extraction;
- automatic subject assignment from the requested Reality Entity;
- trust or factual correctness claims for schema-valid model output;
- changes to evidence attribution, freshness, conflicts, or confidence;
- database migrations, API request changes, or public model configuration;
- persistent entity resolution or a Reality Graph.

These are independent future steps requiring benchmarks and trust boundaries.

## Validation and completion

Step 207 is complete only after the feature passes the repository's full
GitHub-hosted backend CI and is safely merged into `main` with the merge
commit validated. Until then, any implementation is provisional.
