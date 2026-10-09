# Step 211 — Semantic Adapter Claim-Budget Enforcement

## Identification grounded in the existing repository

After verifying the completed Step 210 `main` code, review of
`backend/app/reality/claim_extractor.py` revealed a missing resource
boundary specific to **configured optional semantic inference**.

`EvidenceClaimExtractor.extract_result()` accepts evidence with either
`status="completed"` or `status="usable"` and deduplicates candidates
before invoking Step 207's optional semantic adapter.

The existing 2,000-unique-claim budget was implemented in Step 184 and
checked **only** when `evidence.status == "completed"`. Consequently,
an injected semantic adapter processing `status="usable"` could be
called for 2,001+ candidate sentences without a per-request invocation
count cap. This bypasses the intended ordering documented by Steps 208–210.

However, Steps 184 and 185 expressly preserved a separate **legacy**
generic extractor contract: `status="usable"` without an injected
adapter is permitted to return more than 2,000 claims. Their existing
regression tests intentionally assert that behavior. An unconditional
claim-budget change would break backward compatibility and is **not**
part of this step.

## Objective

Close the optional semantic-adapter invocation budget bypass on
`status="usable"` without changing legacy no-adapter extraction or
altering source attribution.

The existing 2,000-unique-claim limit now governs extraction when:

1. Evidence has `status="completed"` (existing Step 184 behavior); **or**
2. A trusted optional semantic structurer is configured on the extractor,
   including when evidence has `status="usable"` (new Step 211 protection).

When neither condition applies, existing legacy `usable` behavior remains.

## Targeted implementation

Changed only `backend/app/reality/claim_extractor.py` application logic.

- Record at extractor construction whether an explicit optional semantic
  adapter is configured. The historical zero-argument construction remains
  valid, and the default no-model semantics remain unstructured.
- Keep source-scoped sentence extraction and cross-source
  case-insensitive deduplication unchanged.
- Apply `MAX_RETRIEVED_CLAIMS == 2_000` to unique candidates before
  **any** adapter invocation whenever a structurer is configured.
- Preserve the existing `retrieved_claim_limit_exceeded` reason when
  low-level extraction fails closed.
- Preserve Step 208's translation to
  `submitted_claim_limit_exceeded` for a validated submitted bundle.
- Do not return partial claims or incomplete claim/evidence links when
  the count exceeds the budget.
- Preserve the complete source reference tuple for accepted deduplicated
  claims and call the adapter only once per unique claim.
- Continue Step 210's 10,000-character *per-claim input limit* as a
  distinct guard for optional adapters.

This is a nine-line net application-code change, not a new subsystem.

## Boundary examples

| Input state | Optional adapter | Unique claims | Expected result |
| --- | --- | --- | --- |
| `completed` | none | 2,001 | `unavailable`, no claims (unchanged) |
| `completed` | configured | 2,001 | `unavailable`, zero adapter calls |
| `usable` | configured | 2,001 | `unavailable`, zero adapter calls (**fixed**) |
| `usable` | configured | 2,000 | usable, up to 2,000 adapter calls |
| `usable` | none | 2,001 | usable (explicit **legacy compatibility**) |
| submitted bundle | configured | 2,001 | `submitted_claim_limit_exceeded`, zero calls |

Repeated identical sentences across sources count as **one** unique
claim. The adapter receives all contributing source references after
global deduplication, not fragmented per-source inputs.

## Regression and integration coverage

`backend/tests/test_step211.py` checks:

- `completed` and `usable` over-budget rejection with an optional
  structurer and **zero adapter calls**;
- explicit preservation of the legacy `usable` no-adapter contract;
- exactly 2,000 unique `usable` claims and exact adapter call count;
- 2,001 unique candidates spanning source-scoped documents;
- 2,000 repeated claims across multiple sources retaining both URIs;
- unavailable claim results cannot form usable evidence links/conflicts;
- submitted-evidence error translation and resource protection;
- actual submitted-evidence Reality State without partial claim graph;
- normal short `usable` evidence still passing its original source
  references through optional semantic processing.

All earlier full-suite tests, particularly Steps 184–185 and
206–210, must continue passing.

## Deliberate exclusions

Step 211 does not:

- remove the historical `usable` no-adapter behavior;
- change public endpoints or add request fields;
- add external ML/LLM/Hugging Face/model providers;
- introduce a new domain model, normalizer, database, or transport;
- assert semantic-model output truthfulness;
- impose model-specific token, timeout, rate, or payment quotas;
- change conflict, source provenance, freshness, or confidence scoring.

The 2,000 unique-candidate cap is a bounded invocation count, not proof
that any configured adapter is fast, accurate, or safe to execute.
Individual model implementations will need their own evaluation,
timeouts, cost controls, and protections when integrated.

## Completion standard

Step 211 is complete only after the entire GitHub-hosted Python 3.13
compilation and pytest suite succeeds on the PR feature head, the PR is
merged into `main`, the merged implementation passes the full workflow,
and the final repository status synchronization is independently
validated on its own exact `main` commit.
