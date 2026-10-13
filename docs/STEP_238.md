# Step 238 — First real original-source-observed neural NLI shadow pilot

## Verified predecessor and honest milestone selection

At start, `refs/heads/main = a026939c5b0be0083d70bf735c31484a50bcdc37`: completed Step237 with **2,619 tests** and **11/11 independently successful exact-final-main push workflows**, including actual real pretrained ONNX NLI on 20 developer-authored pairs. No previously defined Step238 file existed. Step237 deliberately did **not** establish authentic original source bytes for the NLI challenge. That is the immediate product gap. Step234 external public HTTPS release remains deferred until after core development, issue #242 OPEN.

## Scoped real functionality

Integrate **the existing reviewed, pinned, quantized pretrained Transformer NLI adapter** with **exactly one independently observed original-source HTTPS capture** in an optional research-only runner, using the existing tightly allowlisted TLS reader and an operator-reviewed known original publisher URL. Unlike Step237, the NLI premise must come only from the actual reader's captured page, not a fixture or caller-supplied snippet.

### Acceptance

1. Explicit `--live` is required before any model download or HTTPS source fetch. Source URL is a compile-time fixed, reviewed original source `https://www.python.org/downloads/release/python-3130/`, not an arbitrary caller URL; instantiate `AllowlistedHttpsSourceReader` with only that exact URL. No new API route, permission, source search, or production model registry integration.
2. Observe HTTPS original-source content **once** with the existing DNS pinning/TLS verification/redirect rejection reader. Validate exact expected URI, body type/bounds, original response SHA256, UTC observed time no more than 1 hour old and no more than 30 seconds future, quote unit hashes and unique **complete normalized source text unit** containing one reviewed stable-release assertion anchor. Reject absent/multiple/oversized/quoted/altered captures before passing any source text to the model. A fetched URL string alone cannot authorize an inference.
3. Evaluate three predeclared short claims on that **same single captured unit**: source-aligned, direct negation, and natural-language paraphrase. Use **evidence as premise and each claim as hypothesis**. Compare the deterministic parser's text-only relation to the *real* three-class NLI inference outputs without ever upgrading production Reality States. Record model predictions, source capture SHA256/time, asserted source URL, unit digest, and explicit non-authoritative caveats. Never print raw publisher excerpt, secrets, raw source body, or untrusted exceptions.
4. The model must be actually loaded from fixed revision and independently verified quantized ONNX SHA via Step237's adapter. No model weights committed, no cache/network on import; optional CPU-only dependencies remain outside Docker/backend defaults.
5. Add adversarial isolated tests using an internally injected fixed reader/model to verify one read, no source on unapproved URL, missing/repeated/quote/stale/future/foreign URI/invalid receipt/malformed model outputs and zero authority promotion; also preserve all old tests.
6. Introduce an independent **12th** exact-SHA CI workflow that actually downloads the pinned model and fetches real Python.org HTTPS through `AllowlistedHttpsSourceReader`, runs all three model inferences, and asserts capture receipt plus observed source unit. Require all twelve workflows to pass on PR head and exact final merged main before completion.
7. Explicitly document scientific limits: one preselected page, 3 developer-authored claims, no independent human semantic labels, no broad/representative model accuracy, no factual truth or publisher endorsement established by model output, no production AI-verification authorization, and no external deployment.

## Explicit non-goals

No claims of calibrated accuracy, automated source discovery, semantic production override, multi-agent system, GraphRAG, LLM user interface, generalized true facts, automatic periodic monitoring or a publicly hosted API. The reader provides observed bytes from a TLS-validated endpoint, **not independent human certification of a fact**. No deceptive sourced claim should be inferred from NLI alone.

## State

**IN PROGRESS** until genuinely observed original-source neural inference and all 12 final-main CI workflows are independently verified. Step238 ✅ applies only to the scoped *real-source grounded NLI research integration*. Step234 external hosted release #242 stays open.
