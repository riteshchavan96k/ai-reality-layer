# Step 253 — First evidence-conditioned factual answer with independent source verification

## Verified predecessor and actual new product capability
Step252 accepted at final `main` `7d675952c8d8c105d63479fa9a100d432e868976`, merged [PR #281](https://github.com/riteshchavan96k/ai-reality-layer/pull/281), full **3,187 backend tests**, 22/22 exact-main successful push CI including real pinned FLAN-T5 and HTTPS Python.org. No historical Step253 specification existed. Step252's LLM transformed a yes/no question that *already contained the answer candidate*; it never extracted an unknown fact from source text.

Step253 adds one first narrow **"When was Python X.Y.Z released?"** evidence-first developer workflow. An authenticated API independently fetches an exact operator-allowlisted official Python release webpage, finds its unique "Release date: ..." field bound to the requested page heading and canonical URL, then returns a strictly attributed original-source receipt. Only then does an explicitly opted-in **real** generative model receive the observed field and propose an answer. The client independently parses the observed field again and permits an ISO date answer only when the model's date agrees exactly.

## Security and epistemic boundaries
1. New typed `ReleaseDateSourceRequest`, source receipt with request-binding SHA-256, captured-content SHA-256, selected field SHA-256 and observation timestamp; no caller-provided text or model-provided citations.
2. Pilot bearer middleware protects `POST /api/v1/reality-state/extract/release-date`. The existing pinned-IP, DNS checked, TLS certificate/hostname verified HTTPS reader retrieves the operator-approved original URL **once**. Redirects and unapproved URLs are not permitted.
3. Exact question and entity must match a conservative explicit Python version format, version-derived official release URL and independent page title. The observed visible source must have exactly one matching heading, a single structurally nearby standalone `Release date:` field, a real parsed calendar day, no matching HTML quotation and valid fresh capture receipts. Duplicate, contradictory, misbound, stale, hidden, quoted or missing fields abstain with no partial citation.
4. The defensive client verifies source URL, request binding, exact quote digest, observation freshness, fixed denial of truth/authorship/general QA flags, and source field/date grammar; a mismatched client response abstains.
5. The real CPU `google/flan-t5-small` model is reused with immutable revision and verified safetensors SHA-256 from Step252. Model receives **only bounded user question and date field**, not raw HTML, URL, bearer or credentials. Generated output is untrusted, and unsupported, malformed or incorrect dates abstain without citation.
6. Successful output is one narrowly `bounded_source_date` plus ISO date and source quote/time/capture receipt, **not externally proven factual truth or authenticated source authorship**. Public generic question answering, autonomous search, scheduled monitoring and publisher signatures are not implemented.
7. The **deterministic parser can already read this single date format**. The new model does not improve factual accuracy relative to that deterministic baseline on this test; it proves the evidence-conditioned model/verification separation for the first unknown-answer question type. Quality expansion must show additional useful coverage before adding larger models/cloud GPUs.

## Evidence and acceptance
- Adversarial `backend/tests/test_step253.py`: real authenticated app, injected source captures, no egress on invalid question/bearer, strict receipt binding, source ambiguity, duplicate heading/date, quotation, wrong page, timestamps, date hallucination and malformed model response; mocked model tests are **not** proof of neural inference.
- Complete `python -m pytest -q backend/tests` regression, preservation of historical workflows, real optional exact-pinned FLAN-T5, and actual Python.org source captured by CI runner `python -m backend.app.evaluation.step253_live_release_date --live`.
- [ ] New implementation and focused tests pass at exact PR head.
- [ ] Full Python backend regression and all **23/23** PR workflows pass at exact head.
- [ ] Real model can extract the release date from independently observed official source and negative auth/source checks abort without extra egress.
- [ ] Review safe fallback/abstention policy and limits; merge PR only after green.
- [ ] **23/23 exact final merged-main `push` workflows success**, full backend logs, and model/source logs independently inspected; final signed-off PR audit comment without another unverified code commit.
- [ ] Only then mark scoped engineering Step253 complete.

**Separate mandatory external staging deployment remains unfinished:** [issue #242](https://github.com/riteshchavan96k/ai-reality-layer/issues/242). No customer-ready or production-ready service is claimed.
