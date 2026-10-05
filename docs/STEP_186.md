# Step 186 — Finite Freshness-Window Integrity Across Evidence Paths

## Objective and why this step is justified

The MVP differentiates fresh, stale, and unknown *observations* of evidence.
Step 181 added explicit observation-age freshness on direct developer-supplied
source documents. Step 183 added strict **positive finite** policy validation
to the configured retrieval API. Steps 184–185 bounded claim-graph
amplification in retrieval and direct submission.

The current code review found a concrete **trust-boundary discrepancy**:
the direct-submitted request model, its domain-level validator,
the retrieval request/provider contracts, the canonical freshness
evaluator and the freshness assessment contract only checked whether
`max_age_seconds > 0`. A positive infinity passes that check, so
`age_seconds <= infinity` classifies even arbitrarily old sources as
fresh. NaN passes `value <= 0` checks but produces unordered or
non-JSON values. A Python integer too large to be represented finitely
could cause overflow during evaluation.

No independently preassigned Step 186 specification exists in the original
high-level MVP plan. The verified discrepancy provides a concrete next
correctness and safety task rather than an invented unrelated feature.

## Safety invariant

Developer or retrieval caller policy
→ preserve **only positive finite** numeric observation windows
→ evaluate source observation age against a real, finite duration
→ fresh/stale/unknown assessments
→ conservative confidence / Reality State.

The system **must not** let NaN, infinite values, booleans, numeric strings,
zero, negative ages or huge unrepresentable integers bypass this invariant.
A missing freshness policy remains valid and leaves freshness unknown.

## Implementation

`backend/app/reality/freshness_policy.py` introduces dependency-free
numeric predicates, with no coercion:

- `is_finite_number(value)`: only Python integer/float values
  representable as finite floats; overflow on enormous integers is caught.
- `is_positive_finite_number(value)`: finite and strictly positive for
  declared freshness policy windows.
- `is_nonnegative_finite_number(value)`: finite and nonnegative for
  measured age durations (including zero).

The shared predicate is enforced at:

1. Retrieval HTTP request input (`RealityStateRequest`) and the
   retrieval orchestration entry point.
2. Developer-submitted HTTP request input
   (`EvidenceRealityStateRequest`), both before Pydantic coercion and in
   its after-validator consistency check.
3. Domain `SubmittedEvidenceBundle.validate_freshness_policy`, so
   direct Python callers cannot bypass the HTTP validator.
4. `RetrievalRequest` and `RetrievalProviderRequest` for
   independently constructed or provider-neutral contract inputs.
5. `SourceFreshnessEvaluator.evaluate_result` itself: no invalid value
   reaches a fresh/stale classification.
6. `SourceFreshnessAssessment` including revalidation of dictionary
   contracts: no non-finite age or maximum age can be persisted in or
   serialized through canonical freshness assessments.

Validation continues raising the existing contract-compatible
`ValueError` for domain code, and Pydantic 422 validation errors
for HTTP requests. Previously valid finite numeric windows and
omitted (`None`) windows are unchanged.

## Regression criteria

`backend/tests/test_step186.py` checks:

- NaN, both infinities, huge Python integers, zero, negative numbers,
  booleans, and numeric strings across API, domain, retrieval request
  contracts, evaluator, and internal assessment contracts.
- Correct behavior for positive finite numeric windows and for exactly
  zero *elapsed* seconds.
- Direct-evidence stale source under a finite window remains uncertain;
  a caller-selected larger **finite** window may classify that same
  explicitly observed source fresh, without claiming it is true.
- No-window direct/retrieval API compatibility and unknown freshness.
- Optional OpenAPI fields remain separate on the two existing endpoints.
- Historical Steps 181 and 183 request contracts remain valid.
- Full GitHub-hosted backend compilation and pytest suite must pass on
  the exact final synchronized `main` commit.

## Design boundaries

Freshness means **caller/provider-reported observation age** under an
explicit policy, not publication age, source authenticity, verification of
source truth, or calibrated factual probability. Finite policies can
deliberately be large; they still do not certify factual truth.

This step does not introduce an external retrieval provider, model,
credential, new endpoint, database, live source verification,
monitoring, deployment, or autonomous capability.

## Completion requirement

Completion requires a reviewed change diff, an isolated PR merged to
`main`, and a successful *full* CI run on the final synchronized
`main` HEAD (not merely a passing standalone Step 186 test).
