# Step 209 — Semantic Structure Method Integrity and Metadata Bounds

## Identified defect

The project is currently at verified Step 208. No Step 209 specification
previously existed in the repository. Inspection of the active Step-206
`ClaimSemanticStructure` implementation exposed two concrete problems at
the Step-207 optional semantic adapter boundary:

1. For a `structured` claim, validation compared the **unnormalized**
   `structuring_method` with the reserved `not_attempted` sentinel.
   A value such as `"  not_attempted  "` was accepted and then trimmed
   to exactly `not_attempted`. This produced a self-contradictory
   "structured but no structuring attempted" canonical claim.
2. The `subject`, `predicate`, and `object` fields were already
   bounded, but the adapter-controlled `structuring_method` and
   `reason` values were **unbounded**. An optional model adapter could
   return arbitrarily large strings, amplifying data into Reality State
   response payloads even with the upstream unique-claim limit.

These are actual integrity and bounded-output defects in a currently
integrated canonical contract, not a reason to invent a new product subsystem.

## Objective

Make Step-206 semantic metadata validation unambiguous and bounded across
typed, mapping-shaped, extracted, serialized, and Reality State pathways,
while preserving all existing default behavior.

## Implementation

Changed only `backend/app/reality/claim_semantic_structure.py` in the
application code.

- First reject a non-string or whitespace-only
  `structured.structuring_method` as before.
- Normalize the method with `strip()` **before** comparing to the
  reserved `not_attempted` sentinel.
- Reject both exact and padded versions of `not_attempted` for
  `structured` semantic claims.
- Bound the **normalized** structuring method to
  `MAX_CLAIM_STRUCTURING_METHOD_CHARS = 256`.
- Preserve the existing strict `unstructured.structuring_method ==
  "not_attempted"` invariant.
- Require a nonempty unstructured reason, normalize with `strip()`,
  and bound it to `MAX_CLAIM_SEMANTIC_REASON_CHARS = 1_024`.
- Preserve existing subject, predicate, and object limits:
  `MAX_CLAIM_SEMANTIC_FIELD_CHARS = 10_000`.
- Retain immutable canonical dataclass representation and backwards
  compatible `ClaimSemanticStructure.validate()` and `to_dict()` APIs.

The new limits are intentionally small for metadata while remaining
much larger than the method names and diagnostic reason codes actually
used in production. This is not a claim that the semantic content is
factually correct.

## Canonical metadata rules

| State | Method | Reason |
| --- | --- | --- |
| `structured` | normalized nonblank string, not `not_attempted`, at most 256 chars | `None` |
| `unstructured` | exact `not_attempted` | normalized nonblank string, at most 1,024 chars |

For example:

- `structured` + `"semantic_adapter"` is valid.
- `structured` + `" semantic_adapter "` normalizes to
  `"semantic_adapter"`.
- `structured` + `" not_attempted "` is invalid.
- A method string longer than 256 normalized characters is invalid.
- A reason string longer than 1,024 normalized characters is invalid.

The length checks apply after whitespace trimming. A reason/method
exactly at its limit remains valid; adding one non-whitespace
character rejects it.

## Integration and failure behavior

`ClaimSemanticStructuringStage` already validates each injected adapter's
output by calling the canonical `ClaimSemanticStructure.validate()` method.

As a result, an injected adapter that proposes the contradictory reserved
method or excessive metadata automatically produces the **existing**
fail-closed `unstructured` / `semantic_structuring_failed` result.
The original claim text, source references, and extraction method survive.
No adapter-exception content or excessive metadata is returned.

This behavior applies unchanged to the source-scoped retrieved-evidence
path and the Step-208 globally deduplicated submitted-evidence path.

## Regression coverage

New `backend/tests/test_step209.py` verifies:

- Exact and whitespace-padded reserved `not_attempted` methods rejected;
- Both typed and mapping-shaped construction paths;
- Correct normalization of valid methods;
- Method boundary acceptance at 256 and rejection at 257;
- Reason boundary acceptance at 1,024 and rejection at 1,025;
- Preservation of the original attributed claim after invalid
  injected-adapter output;
- Failure-closed rejection of oversized method and reason metadata;
- Default no-model/unstructured behavior unchanged;
- Canonical claim serialization and mapping round-trip validation;
- End-to-end submitted Reality State serialization for both valid and
  invalid injected semantic metadata.

The project's **full** historical regression suite must pass,
especially Step 206–208 tests.

## Non-goals

This step deliberately does **not** add:

- Another parser, provider, normalizer, or domain contract;
- ML, DL, Hugging Face, LLM inference, or network activity;
- Source authenticity or semantic accuracy certification;
- New model execution configurations or external API fields;
- Entity resolution, semantic conflict detection, or knowledge graphs;
- Database or retrieval behavior changes.

Future advanced semantic integration should use these bounded
contracts, but actual model integration requires its own scope and
evaluation.

## Completion criteria

The change must pass the repository's complete GitHub-hosted Python
3.13 compilation and pytest workflow on the feature branch, merge via
a reviewed PR, pass again on merged `main`, and complete a final
status-sync commit validated on its exact `main` SHA.
