# Step 220 — Observed Independent Source Text Gate Scorecard

## Exact hosted results

**First successful branch workflow:** [run 37999041855](https://github.com/riteshchavan96k/ai-reality-layer/actions/runs/37999041855) on feature SHA `6fd1e4774367895ad870fb5c4cf4c4f1d86260f7`.

- Complete Python 3.13 backend compilation succeeded.
- **2,099 backend regression tests passed** in the initial branch run.
- Historical Step 217 and Step 218 standalone benchmark runners passed without changing their original inputs or recorded baseline scorecards.
- The new Step 220 **48-case controlled backend-reader replay** succeeded and the actual printed JSON was saved unchanged to `docs/STEP_220_SCORECARD.json`.
- A subsequent test now asserts the scorecard equals a fresh 48-case replay; the final feature head must still pass that new test before merge.

The Step 220 result is **conditional**: its observer is a deterministic, separately provided backend callback containing the **reviewer-authored reference summaries** stored in the Step 218 dataset. These text bodies were *not* fetched, captured or authenticated from original publishers. The callback is isolated from the *submitted adversarial documents*, but its reference summaries are author-created fixture content, not blind independent-world evidence.

## Measured scores for opt-in strict mode

| Measure | Controlled results | Interpretation |
| --- | ---: | --- |
| Unsafe `supported` decisions in 40 abstention-required scenarios | **0 / 40 (0%)** | Given simulated independently returned reference text |
| Correct structural support on eight curated relevant texts | **8 / 8 (100%)** | Exact-match observer configured and source identity aligned |
| Legitimate cases supported **with NO configured reader** | **0 / 8 (0%)** | Intentional fail-closed default: all abstain |
| Entire submitted source text matched all required observed content | **32 / 48** | This is an exact quote/substr condition, **not truth verification** |

### Comparison with Step 219

Step 219's **non-strict** historical Step 218 replay remains recorded
at 8/40 unsafe structural `supported`, all eight of those being
forged content under a plausible genuine official URL.

The opt-in Step 220 strict mode using **known separate simulated reference
text** now requires an exact quote match, so those eight fabricated
statements do not pass. The original on-topic eight examples still pass
conditional on the independently supplied fixture text.

**These are not exchangeable production-performance numbers**:
Step 219 measured the legacy mode and Step 220 measures a new opt-in
mode with a specifically curated test observer. Claiming that the
product has solved publisher-content authenticity or achieved zero
real-world false support would be false.

## Fail-closed behavior

For strict API requests with no independently configured backend
source reader—the actual prototype default—every document's
`independent_source_text_assurance` status is `unverified`.
This downgrades the overall status to `uncertain` regardless of
correct source attribution, timestamps and explicit entity text.
Thus both forged and legitimate source statements abstain. That is a
deliberate assurance-versus-availability tradeoff, **not** production
readiness.

Errors are explicit: unconfigured provider, failed callback,
invalid content, too-large content, mismatched URI, or absent exact
excerpt never grant support. A source hash sent by the caller cannot
pass the check. One mismatch among multiple submitted sources fails the
aggregate requirement.

## Remaining technical and product work

The Step 220 mechanism **does not implement** a safe operator-hosted
HTTPS publisher fetch, authenticated source snapshots, parsing original
HTML, content timestamps, cryptographically verifiable publisher
signatures, task entailment or factual truth checks. A dishonest
backend reader could echo a false submitted document, and exact matching
would accept its assertion as observed.

The next important engineering milestone should be to **actually
connect a safe, bounded, operator-owned original content reader**,
with allowlisted origins, controlled redirects, DNS/SSRF protections,
response MIME/size bounds, tested retention and audit timestamps,
and a meaningful source capture artifact. Evaluate on separate actual
original-source captures with independent human-reviewed annotations
and retained legitimate-support coverage, not only failure cases.

The benchmark comparison has value as a **verified trust-boundary
regression**; it does not mean the global AI Reality Layer objective is
already achieved.

## Reproduction

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
```

The scorecard and raw counts in `docs/STEP_220_SCORECARD.json`
come from the first hosted workflow, not estimated values.
