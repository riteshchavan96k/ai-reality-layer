# Core product slice: claim -> original source -> Reality State

**Status:** Incremental core engineering proposal. Not a historical Step 235 specification, not a general-purpose fact checker, and not Step 234 external deployment completion.

## Why this slice

At the verified Step 233 / deferred Step 234 checkpoint, clients of `/api/v1/reality-state/evidence` must supply their own excerpts. Those excerpts are untrusted and independently checked, but this leaves real original-source excerpt selection outside the AI Reality Layer. This slice moves the selection of a **single bounded original-source assertion** into the backend without giving an LLM, browser or arbitrary URL authority.

## Opt-in API

`POST /api/v1/reality-state/claim` with the existing Step 231 pilot bearer gate:

```json
{
  "entity": "Python 3.13.0",
  "claim_text": "Python 3.13.0 is a stable release.",
  "source_uri": "https://www.python.org/downloads/release/python-3130/",
  "freshness_max_age_seconds": 3600
}
```

The request has **no caller-supplied excerpt**, attestation, observation time or digest. The explicit source URI is only a *candidate*: it must match an exact HTTPS URL configured by the operator through `ARL_INDEPENDENT_SOURCE_ALLOWED_URLS`. The endpoint **does not discover arbitrary web pages** or automatically identify the right official publisher. Operators still own source selection and review.

### Security and functional behavior

1. Validate claim, explicit entity, safe HTTPS URI and bounded positive freshness policy. Reject unknown request fields.
2. Parse only the established conservative atomic claim grammar. Unsupported claims abstain **without making network requests**.
3. Build the existing backend-configured original HTTPS reader. If none exists or source URL is off its exact allowlist, return an **unavailable** response and perform no source fetch. Never use `source_uri` to create a new reader or authorize arbitrary destinations.
4. Make exactly **one** real source observation through `AllowlistedHttpsSourceReader` (operator URL allowlist, globally routable pinned DNS, TLS and hostname verification, bounded bytes/time, blocked redirects, hidden HTML and quote provenance handling). No secondary lookup to select evidence.
5. Walk structural text lines from the server-captured body. Select only if **exactly one complete line** has an atomic relationship to the claim under the existing bounded parser. If there are zero or multiple relevant lines—including an explicit opposite line—abstain, rather than cherry-pick. Do not synthesize unobserved excerpts.
6. Reuse the same immutable-in-request server capture in the existing `IndependentSourceTextAssurance` and `build_reality_state_from_evidence` pipeline. This prevents network drift between excerpt selection and final source receipt. The previous unique text-unit guard, HTML quote digest, source counterstatement policy, observation receipt, freshness, explicit-entity relevance and claim alignment still decide whether a claim is supported.
7. The response is a compact status and reason plus `reality_state` when a unique bounded candidate was evaluated. With no unique candidate it returns `reality_state:null`. A source fetch or text match **alone** never means supported.

### Conservative limitations

- One user-designated **operator-allowlisted** original-source URL, one source snapshot, one bounded relevant source unit. No crawling, LLM reasoning, open-world entity/source search or automatic semantic paraphrase.
- A page may be true and relevant but fall outside current grammar; abstention is correct. Conflicting/duplicated assertions are rejected, even if this reduces positive coverage.
- Independently fetched HTTPS is not publisher authorship proof or factual truth. `semantic_support_verified` and `factual_truth_verified` remain false.
- HTML text extraction is conservative, not a complete browser CSS/JS engine; some pages will abstain.
- Offline integration tests mock upstream reader observations. A **new independent GitHub Actions workflow**, `.github/workflows/core-claim-only-live.yml`, executes the new authenticated claim-only route against the real Python.org original publisher over verified HTTPS. It requires one genuine bounded positive and safe refusal of its negation and reports only redacted policy flags. Passing PR and exact merged-main run evidence must be verified before declaring this live product slice accepted; it is **not externally hosted**.
- External staging, human-labeled factual accuracy and general-purpose claim verification remain **not done**. [Step 234 and #242](STEP_234.md) are deferred external deployment acceptance, NOT completed.
- Avoid sharing source evidence outside permitted uses and publishing raw source pages or credentials.

## Engineering acceptance requirements

- New route is bearer protected in pilot mode; development has no independently configured reader unless explicitly allowlisted.
- Atomic positive, negation, ambiguous/multiple units, quoted unit, stale observation, unsupported claim grammar, wrong URL and reader failure produce bounded expected behavior with a **single** source read at most.
- New and old backend tests and historic real-original-source GitHub workflows pass on the exact final main SHA.
- Verify independently against a genuine original publisher in a separately authorized canary before stating that this specific route has live-HTTPS integration evidence.
- Any next iteration must be driven by observed safe-abstention failures and real AI-client utility, rather than adding arbitrary components.
