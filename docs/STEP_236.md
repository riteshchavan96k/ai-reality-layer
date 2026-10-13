# Step 236 — Semantic verification benchmark foundation, blind-review contract, and deterministic baseline

**Milestone definition established before implementation from verified repository evidence.** At start, exact `main` `a8404868b8669cedd349412120727988f6855a40` had 2,550 green backend tests and nine successful exact-SHA original-source/API CI workflows. [Step 235](STEP_235.md) was latest completed scoped engineering milestone. Step 234 external hosting remains intentionally deferred, with release [#242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) OPEN. No pre-existing Step 236 description was present in the repository. This is a **new bounded engineering scope** based on documented [Step 217](STEP_217_BASELINE.md), [Step 232](STEP_232_SCORECARD.md) and Step 235 evidence gaps.

## Product problem

A strictly observed source and a successful bounded source claim gate still lack general **semantic entailment/contradiction** capability. The fixed, developer-authored earlier benchmark has 1/2 supported positives, including a true release-date statement that current grammar cannot parse. An LLM or pretrained NLI model cannot be accepted solely because it says "entailment." We must be able to run the *current actual claim-alignment grammar* on a frozen, independently labelable case collection and use the **same case IDs and labels** to evaluate future models.

## Precisely deliverable engineering scope (not independent human accuracy)

1. Freeze 20 **explicitly non-independent** candidate claim–evidence pairs: twelve derived from Step 232 (two original publisher URLs with developer-authored quoted/forged/insufficient cases), plus eight clearly synthetic paraphrase/negation/neutral/hedged challenge pairs. Each case contains a unique stable ID, entity, claim, source-scoped evidence text, source reference, and `evidence_origin`. The corpus MUST NOT include model predictions, ground-truth semantic labels, or invented human reviewers. Original publisher URL in Step232 is **not** proof that all the submitted candidate excerpt text appeared on the real page.
2. Add deterministic baseline runner that invokes the **existing actual** `_parse_atomic` and `_relationship` without replacing production verification; returns `bounded_alignment`, `bounded_contradiction` or `abstain` for every case. Treat this as a **text-comparison research baseline**, not externally verified source/Reality State factual support.
3. Make a reproducible blinded-review packet containing only case IDs, claims and excerpts, without predictions or former Step 232 expected outcomes. Packet contains a dataset digest. Its metadata does not claim a neutral independent annotator exists.
4. Add strictly validated reviewer-submission schema with up to two independent *role-declared* external reviewer IDs per case, one of `entails`, `contradicts`, `neutral`, `uncertain` and no free-form raw-text labels. A review never becomes **independently authenticated** simply because its JSON declares a reviewer; the system cannot verify human identity or independence. Require distinct IDs, complete coverage, two **agreeing** labels for every case before conditional scoring. Otherwise fail closed to review `incomplete`/`disputed`, **no** implied quality pass.
5. Report per-class counts and exact numerators/denominators for `bounded_alignment` against consensus labels, including false support and abstention. Keep the **conditional-scoring** caveat: external reviewer identity, dataset representativeness, source truth, and factual accuracy are NOT authenticated. No magic target percentage or model confidence.
6. Test dataset mutation/unknown case labels, model-prediction leakage, digest mismatch, reviewer spoof/duplicate, missing or conflicting labels, zero-division, incorrect false-support counts and 20-case stable baseline. Run standalone new CI workflow on PR and merged-main SHA alongside nine existing workflows.
7. Document human review protocol and next legitimate milestone: *actually recruit independent annotators, verify their authorizations and labeling provenance offline, adjudicate disputes, freeze holdout and perform measured NLI comparison in shadow mode.* No private identifiable review data committed, no remote inference or model downloads, no cost/secrets/deployment.

## Security / truth boundaries

- Corpora are constrained developer-written short pairs with no executable untrusted source data, source retrieval, credentials or network calls.
- Real publisher URLs in the challenge are **source candidates**, not certificates of corresponding evidence bytes; developer-crafted forged counterexamples are intentionally included.
- Reviewer JSON is an **untrusted input** and self-reported independent identity cannot be proven by this module. Comparison to voluntarily submitted annotations is **conditional**, not verified field accuracy.
- The runner never upgrades original-source production support decisions, bypasses user-approved source allowlists, or authorizes external AI actions.
- A green test suite validates benchmark tooling only. It does not close Step 234 deployment release gate or establish NLI performance.

## Completion criterion

Freeze corpus and blind packet generation; produce baseline on all twenty with real deterministic parser, prove robust fail-closed review/metrics tests; confirm all new + historical tests and workflow gates green on the exact merged-main SHA. **Step 236 engineering completion may be marked ✅ only for this scoped foundation.** **Independently completed human review and factual accuracy must remain pending until real independent review is provided, audited, and measured.**
