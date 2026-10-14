# Step 242 — Fail-closed source-cited answer consumer for developer AI applications

## Verified predecessor and evidence-based scope

On 15 October 2026, the actual main branch was `980de748b8cf396b26d3b1cee230214b819f56ce`. Step 241 was the latest completed scoped engineering milestone; all **15 final-main push workflows succeeded**. Its core answer API came via implementation PR #264 and acceptance PR #265. The preceding Step 241 proof is at [docs/STEP_241.md](STEP_241.md). There was **no existing Step 242 specification** on main. The requested `docs/STEP_241_SCORECARD.md` does not exist; its acceptance evidence is documented in STEP_241.md and the GitHub workflow logs.

Step 241 made a bounded cited answer *available on the server*, but no typed, application-facing consumer could call this endpoint and independently reject malformed, misattributed, stale, or secretly upgraded citations. Earlier Step 235 and Step 240 integrations consumed the **claim** endpoint, not the Step 241 **answer** endpoint. This is an actual integration gap for an AI developer, unlike another paper-only verification contract.

## Implemented scoped functionality

- Add `backend/app/integrations/cited_answer_client.py` with `check_cited_answer_with_api(client, token, request)`, a single authenticated POST to the Step 241 answer endpoint through an injected trusted HTTP client. Never fetch the publisher in the client, choose arbitrary server URLs, download models, or take AI actions. The caller MUST supply an authentic local transport or verified-HTTPS transport and protect the bearer token. The client does **not** implement TLS or authenticate the server itself.
- Parse the strict typed answer schema and independently verify the **exact request-binding digest**, fixed wording matching support/contradiction/abstention, complete citation presence, exact URL binding, quote UTF-8 SHA256, safe one-line quote, capture UTC timestamp and maximum age, and literal false epistemic ceilings. Refuse mixed, expired, forged, malformed, extra-field, oversized, non-JSON, unauthenticated and otherwise unsupported responses.
- Return an immutable, application-consumable `ClientCitedAnswer`, including static bounded answer text and a `CitedSourceObservation` with exact original-source quote and observational digests only after all checks pass. An explicit contradiction is **not** treated as permission to assert source support; all other cases abstain and suppress quotes and URIs.
- Add independent adversarial API integration and transport tests, preserving all old routes and consumer logic.
- Add a dedicated `--live` canary with actual Python.org TLS → authenticated local FastAPI → downstream client. The canary checks positive/contradiction/unsupported/unapproved/bad authentication without printing raw publisher text or credentials.
- Add a **sixteenth GitHub Actions workflow** to execute tests and the genuine HTTPS client canary. Require all existing regression workflows and full backend suite to pass on the exact **final merged main SHA** before accepting Step 242.

## Epistemic and security limits — never infer more

This is **not** a signed publisher receipt or a second independent corroboration source. An unkeyed SHA256 proves internal quote-byte consistency, not origin authentication; an attacker who controls an untrusted transport could rehash forged data. The caller must verify server identity through a trusted transport. The source may be inaccurate, semantically misleading, or compromised. The fixed original-source claim grammar remains narrow. Quote text is **untrusted data**: clients must HTML-escape any rendered output, never interpolate it into system prompts or execute it.

No multi-publisher corroboration, human-relabelled source domain accuracy, unsupervised LLM support, arbitrary web search, external hosting, automatic actions or general factual truth is claimed. The Step 234 external release gate remains **deferred** at owner request; [issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) is a GitHub issue number, **not** the Step 242 milestone.

## Required acceptance evidence

The service and test code are provisional until reviewed. Verify: complete backend regression count from actual GitHub log; dedicated Step 242 tests; the live genuine publisher canary; and every *push*-event workflow success with `head_sha` matching exact merged main. A successful PR head alone is **not** final-main acceptance. Do **not** mark Step 242 complete until these checks have passed. Record follow-up audit in PR without introducing an unverified post-acceptance commit.
