# Step 252 — First real generative LLM candidate with fail-closed original-source claim verification

## Independently verified starting checkpoint

At scope selection, current `main` was `21b8fa0bf793d5f98d65e560f45c1694f158227b`, accepted Step 251 [PR #280](https://github.com/riteshchavan96k/ai-reality-layer/pull/280). Its 21/21 exact-main push workflows passed; original backend logs recorded **3,157 passed**; dedicated history logs showed **186 passed** and three genuine official Python.org HTTPS captures. No `docs/STEP_252.md` or Step 252 implementation was present. Historical project conversations established priorities of real functionality, secure source verification, genuine neural inference and later LLM integration. Step 234 externally hosted deployment remains deferred; mandatory [issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242) remains open.

## Product limitation and scope

The core model catalog exposes only `mock-model`. The real Step237 pretrained ONNX Transformer is **NLI classification**, not generative; Steps241/242 return conservative fixed cited source statements for explicitly supplied atomic claims. A developer cannot use a *real generative model* to propose a claim from even a narrow yes/no question and then independently check it against one genuinely observed original publisher source.

Deliver the smallest end-to-end, explicitly opted-in **local developer integration**:

- A real instruction-tuned FLAN-T5-small model runs in an isolated, optional CPU-only adapter. Its reviewed Apache-2.0 Hugging Face model revision `0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab` is immutable; the only allowed weight file `model.safetensors` is checked against SHA-256 `495fa51e204676f1a857a9fc13c4c89f3f5ba9f480b898cebca02add25e6d749` before deserialization. Only explicitly enumerated tokenizer/config files may be acquired. Never allow remote executable model code or unsafe pickle weights, model downloads on import, or production server auto-loading. Optional pinned CPU packages run only in the new standalone CI workflow, **not** the base backend/Docker image.
- New `check_question_with_grounded_llm(client,token,question,entity=...,source_uri=...,model=...)` accepts a **single narrow yes/no property question**. A deterministic, independently parsed atomic proposition captures the question's entity, polarity, verb and property *before* model execution. A real model proposes a declarative claim. The candidate is admitted only when the established Step227 parser proves it matches the complete original question's atomic meaning; unexpected version, polarity, property, reported speech, multiple sentences, wrong entity and prompt-injection-shaped text must abstain **without any publisher fetch**.
- The model sees only the bounded question, never the bearer or untrusted original publisher HTML. A candidate passing the question gate is sent through the existing Step242 **authenticated** cited-answer client. It independently verifies a server-allowlisted original-source HTTPS observation, the exact selected nonquoted source unit, any counterstatement, request-binding SHA256, source capture + quote hashes, observation freshness and static authority flags. The client only performs **one original-source API call/read** on a valid candidate. No model-supplied citations or guessed publisher quotes may pass.
- The final dataclass explicitly distinguishes `bounded_source_support`, `bounded_source_contradiction`, and `abstain`. Only an independently supported source receives `may_use_as_bounded_evidence=True`. Publisher contradicting a generated claim cannot be upgraded; all failed source checks reveal no quote or source metadata. Even positive results are bounded textual source observations, NOT authenticated publisher authorship, semantic fact proof or general open-domain truth. Generated text is always treated as untrusted and never interpolated into instructions.
- `backend/tests/test_step252.py` exercises real authenticated FastAPI with injected source captures, exact one-read receipts, contradiction, a variety of generated drift attempts, invalid natural-language forms, arbitrary/off-allowlist sources, invalid auth, source ambiguity/errors, model exceptions, and digest-model loader refusal. No optional neural packages are imported or downloaded by the default suite.
- The new 22nd GitHub workflow installs optional pinned model packages only inside the CI job, fetches genuine *SHA-verified* FLAN-T5-small weights with explicit `--live`, actually generates a claim from `Is Python 3.13.0 a stable release?`, then verifies it by the existing authenticated local FastAPI + **genuine original Python.org HTTPS** reader. The produced candidate must be independently source-supported in the bounded policy; incorrect authentication, unapproved URL and out-of-scope question must abstain. Logs contain audit booleans only, not raw publisher text, model output, secrets or untrusted exceptions.

## Reproduction and security

The ordinary regression needs only existing backend dev requirements:

```bash
python -m pytest -q backend/tests/test_step252.py
python -m pytest -q backend/tests
```

Real model runtime is opt-in and resource heavier; use the pinned optional versions in `.github/workflows/step252-real-generative-grounding.yml` and:

```bash
python -m backend.app.evaluation.step252_live_llm_question --live
```

Do NOT use this module as an unauthenticated public LLM API. The transport, bearer, source allowlist and rate limits remain an operator responsibility. Unsupported questions, varied prose, complex multi-clause questions, new source discovery, generic LLM reasoning, multiple entities, independent verified publisher ownership and customer-facing external hosting are **not** established.

## Exact acceptance gate

- [ ] PR implementation and focused offline adversarial tests pass with existing backend compatibility.
- [ ] Full Python backend regression passes without changing existing 21 workflows.
- [ ] Exact PR SHA runs real verified FLAN-T5 CPU inference and captures real HTTPS Python.org through authenticated cited-answer client, including strict fail-closed negative cases.
- [ ] Review diff and security boundaries; merge only once green.
- [ ] Independently check **22/22 successful exact final merged-main `push` GitHub Actions**, full backend logs and real-source/model job logs.
- [ ] Record the accepted SHA in a merged PR audit comment, without another unverified code commit. Only then give Step 252 ✅.

External deployment Step234 and issue #242 remain OPEN. This single yes/no feature is a **first genuine generative integration**, not broad semantic factual reliability or deployed AGI.
