# Step 210 — Bounded Optional Semantic Structuring Input

## Verified gap in the completed Step 209 repository

Step 207 introduced an injectable semantic structurer; Step 208 ensured global claim
deduplication and the 2,000-claim budget run before optional inference; Step 209
bounded method and reason output metadata.

The remaining gap is an **unbounded inference input within a bounded document**:
the existing accepted source-scoped evidence document may contain as many as
50,000 characters, and the deterministic sentence extractor may legitimately
emit one 50,000-character claim. Previously the Step 207 stage passed this entire
text to any injected semantic adapter without a separate input-size policy.

Large inputs can be expensive or incompatible with real NLP/ML/LLM systems. The
evidence and claim should stay intact: silently truncating a sentence before
parsing would risk inventing incorrect semantics.

This step is chosen from that inspected code gap, not a pre-existing named
roadmap step or a request to add a model.

## Objective

Limit the number of characters sent to an **optionally configured** semantic
structurer while preserving:

- original evidence and complete candidate-claim text;
- original source URI attribution, including deduplicated sources;
- all prior claim graph/document budgets;
- zero-model default behavior;
- normal inference for in-bounds candidate claims;
- fail-closed, explicit unstructured output for skipped claims;
- current request/response contracts.

## Implementation

Change only `backend/app/reality/claim_semantic_structurer.py` in application
code, without a new service, dependency, provider, API input, or adapter protocol.

- Introduce `MAX_CLAIM_SEMANTIC_INPUT_CHARS = 10_000`.
- In `ClaimSemanticStructuringStage`, recognize whether a trusted optional
  structurer was supplied at construction.
- Continue existing claim-text and source-reference validation first.
- If a **configured** structurer would receive more than 10,000 characters,
  **do not invoke it**; return canonical:
  `unstructured` with `reason="semantic_structuring_input_too_long"`.
- Exactly 10,000 characters remains permitted (inclusive upper bound).
- Never truncate or replace candidate text or modify source refs.
- A default unconfigured stage continues to use the
  `NotAttemptedClaimSemanticStructurer` outcome, even for long claims:
  `unstructured` / `semantic_structuring_not_attempted`.
- Existing Step 207 no-result, malformed-result, and exception failure
  behavior is unchanged for claims inside the input budget.
- The 10,000-character policy counts Python string characters, **not tokens**.
  It is a conservative generic input guard, not a universal model token limit.

## Execution order

```
source-scoped, validated retrieved or submitted evidence
  -> deterministic candidate sentence extraction
  -> global duplicate merge with complete source attribution
  -> global claim count budget
  -> Step 210 optional adapter input-length check
     -> too long: preserve claim and mark semantic structuring skipped
     -> in bound: Step 207 adapter invocation, Step 209 output validation
  -> canonical claims / links / Reality State
```

The submitted evidence path uses the shared extractor after Step 208, so
the new policy covers both retrieval and developer-submitted evidence.

## Why skip rather than truncate?

A raw sentence may contain vital modifiers or negation near its end.
Truncating it before a model processes it could yield a syntactically valid
but semantically incorrect subject/predicate/object triple.
Explicit abstention maintains the original evidence and avoids false semantic
certainty.

## Regression tests

`backend/tests/test_step210.py` includes:

- the exact 10,000-character boundary and 10,001-character rejection;
- a recording adapter proving no invocation occurs for an oversized claim;
- default/no-model behavior remaining unchanged;
- exact original claim text, size, and source refs preserved on rejection;
- valid short claims still structured alongside skipped long claims;
- shared long claims from multiple submitted sources merged before the guard;
- combined long/short multi-source submissions, with one adapter call only
  for the unique in-bounds claim;
- source-reference validation still occurring before the size gate;
- end-to-end developer-submitted Reality State output and source lineage;
- end-to-end no-model and in-budget adapter compatibility.

Full historical regression coverage is required, especially Steps 206–209.

## Non-goals / honest limits

This step does NOT add Hugging Face, ML, DL, an LLM, new external retrieval,
entity resolution, semantics verification, model-specific token accounting,
provider-specific context windows, timeouts, concurrency control, pricing
controls, source credibility ranking, or prompt-injection defenses.

The existing optional adapters remain trusted in-process dependencies.
A character bound does not prove semantic correctness, factual accuracy,
or that future provider-specific resource limits are sufficient. Future
real-model work must provide those protections as needed.

## Completion

The change is complete only after the complete GitHub-hosted Python 3.13
backend workflow passes on the feature branch, PR is merged into `main`,
the merged implementation passes the complete workflow, and the status
synchronization commit passes the same workflow on its exact `main` SHA.
