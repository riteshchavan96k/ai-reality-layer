# Step 149 — Canonical Blocked Retrieval Result

## Objective

Make the retrieval engine's blocked provider-selection outcome use the canonical retrieval-result contract.

## Problem Found

After Step 148, the not-required path and provider execution outcomes used the canonical retrieval-result contract, but the provider-selection rejection path still constructed a raw dictionary in _blocked_selection_result().

That left a remaining retrieval-result construction path outside the canonical validation boundary.

## Implementation

Step 149 changes _blocked_selection_result() to call RetrievalResultContract.blocked().

The blocked result therefore enforces:
- status="blocked";
- no provider identity;
- empty sources;
- no content;
- retrieval_executed=False;
- a nonempty reason.

The existing selection behavior is unchanged: a selection that is not executable remains blocked and no provider is executed.

## Safety Invariant

provider selection not executable → canonical blocked retrieval result → retrieval_executed=False

## Regression Coverage

Dedicated Step 149 tests cover direct blocked-result canonicalization, blocked-result execution/payload semantics, and engine integration when provider selection is not executable.

## Scope Discipline

No new network behavior, provider, credential, LLM, RAG, embedding/vector database, semantic truth verification, ML/DL, or model execution is introduced.

## Validation Truth

Dedicated regression coverage is committed. Local pytest execution has not been performed in this session. GitHub status checks are not configured, so no automated test-pass claim is made.
