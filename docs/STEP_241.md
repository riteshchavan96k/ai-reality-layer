# Step 241 — First authenticated, source-cited bounded answer API

## Repository verification / why this is the next correct milestone

Before defining Step 241, independently refetched `main` as exact SHA `d12869e76aec0a09d923911b758515ee564e9439`, following merged implementation PR #262 and acceptance PR #263. **All 14 exact-final-main GitHub Actions `push` workflows succeeded**, including 2,740 backend tests and actual original-source HTTPS → authenticated FastAPI → real NLI veto. [Step 240](STEP_240.md) was the latest completed engineering milestone. No existing Step 241 specification was found. Step 234 externally hosted rollout is **intentionally deferred** until core product completion, and [release issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) remains OPEN.

## The real product gap

The verified claim API and developer SDK can make a decision and expose a source quote, but an AI application still has to invent its own **human-readable, correctly attributed answer and citation**. That risks transforming narrow `bounded_supported` into categorical factual-truth assertions, fabricating quotes, or citing sources after the underlying verification refused them. Add a *first composable, actually usable answer endpoint* reusing the existing one-capture source-assured claim pipeline, with **zero free-form language-model generation**.

## Exact engineering scope

1. Add authenticated `POST /api/v1/reality-state/answer`, reusing the existing validated `OriginalSourceClaimRequest` including entity, claim, exact operator-allowlisted source URI, and freshness limit. It must call the existing `verify_original_source_claim` **exactly once** per HTTP request, never refetch a publisher and never skip the existing HTTPS allowlist, original source text selection, HTML quotation, conflict, and freshness gates.
2. Construct a typed `BoundedOriginalSourceAnswerResponse` **from the one returned claim result**, first applying Step235's complete `interpret_claim_reality_state` trust gate to that exact validated request. Only `bounded_supported` and `bounded_contradicted` states may display bounded cited original-source text. Independently check `source_evidence` text length/UTF-8 SHA256, exact capture receipt/UTC timestamp, and source URI; reject extra or malformed fields, ambiguous/quoted/unsupported evidence, and invalid claim request binding.
3. Use only two **static, carefully worded templates**: the observed source statement *aligns with* or *contradicts* the submitted claim **under a bounded policy**. Do not rewrite claims, paraphrase original text, invent context, assert that something is actually true, claim author signature, or add any neural support. Return an exact bounded source quote, source link, capture SHA256 and time as **data fields**, not LLM-generated citation markup.
4. All failed/unavailable/incomplete cases must **abstain**, using one fixed text-only abstention template and **no quote, citation, publisher URL, capture digest or timestamp**, including malformed receipt or source evidence, wrong auth, off allowlist, unsupported grammar, stale/quoted/ambiguous/counterstatement source content. The request binding digest stays available for routing but **is not authentication**.
5. Preserve Step240 opt-in neural veto separate from the answer endpoint; a deterministic source-cited answer is **not** proof of semantic or factual truth. A language model must not use this new route to promote an unverified claim. The resulting answer object is safe to display as an attributed source observation, not as an autonomous decision.
6. Add real authenticated FastAPI adversarial tests for positive/contradicted/unsupported/off-allowlist/wrong authentication; no extra source read, timestamp and digest binding, tampered claim state and source excerpt suppression, fixed templates, no prompt-injection interpolation, and backwards compatibility. Add 15th CI workflow proving real Python.org TLS → authenticated answer endpoint, both source-positive and source-contradicted citations, unsupported/denied abstentions and no leaked source content. Require **15/15 exact merged-main workflows** and passing full backend tests before Step 241 ✅.

## Nonclaims / future work

- The model still only supports narrow deterministic atomic source-alignment grammar and fixed, operator-allowlisted URLs. This is **not** open-domain question answering, a general live fact checker, a generative LLM response, a multi-source independently corroborated fact, or a deployed customer application.
- A matching publisher page and a cryptographic capture digest demonstrate one observed response, **not authenticated authorship or factual truth**. A source might be inaccurate.
- No user-provided arbitrary source URL fetch. No external release, Docker/ML dependency changes, or model-to-production authority promotion.
- Future genuine capability gaps: multi-source corroboration, diverse source discovery and independently human-reviewed domain-specific source+claim evaluation; temporal real-world history; calibrated model use if justified.

**Completion gate:** confirm actual live workflow, all historic regression gates and exact final-main 15/15 success, then mark **✅ Step241 engineering answer endpoint complete within this narrowly bounded scope**.
