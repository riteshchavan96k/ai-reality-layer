# Step 220 — Opt-In Independent Source Text Assurance Boundary

## Why this step

The verified Step 219 repo's source-anchored controlled benchmark showed
**8/8 attacker-authored claims under a genuine publisher URL** still marked
`supported`. Explicit entity alignment made wrong-topic evidence safer
but could not establish that a **caller-supplied source claim appears in
original source content**. A URI and its hash are not authentication.

The concrete next step is to allow a developer to opt into an **additional
fail-closed comparison** between each submitted evidence excerpt and text
returned by a separately configured, **backend-controlled** source reader.
This is a real enforcement boundary. **It is not yet a general publisher
authenticity service**: a production-grade independent source reader must
still be installed and reviewed by the operator.

## New behavior and trust boundary

`POST /api/v1/reality-state/evidence` now accepts an optional literal bool:

```json
"require_independent_source_text_match": true
```

When omitted or `false`, existing submitted evidence processing and all
historical Step 217/218/219 benchmarks are unchanged.

When `true`, for **each** submitted source document:

1. The backend's independent reader is called with the canonical submitted
   source URI. Reader behavior is installed by backend code through
   `OrchestrationDependencies.independent_source_text_assurance`. The
   public request cannot supply a reader, matching results or hashes.
2. The reader must return a mapping with the **exact** same URI and a
   nonempty separately obtained `content` string, at most 200,000 chars.
3. The **entire submitted excerpt** (trimmed per existing rules) must
   appear contiguously in the reader-observed text. Merely repeating an
   entity, sharing a URL, or supplying a SHA256 hash cannot pass.
4. A matching source receives `exact_text_observed` and a SHA256 of the
   **reader-returned content**, not caller-provided content. This digest
   makes the local reader-returned bytes auditable; the hash alone does
   not authenticate a publisher.
5. All sources must match for the aggregate `exact_text_observed`.
   Otherwise `unverified` forces overall `uncertain`, even when link
   coverage, freshness, entity alignment and conflict count would
   otherwise imply `supported`.
6. No configured reader, provider exceptions, invalid response,
   wrong URI, oversized bytes, or missing excerpt **fail closed**.
   Raw provider exceptions are not exposed in the public response.

The result is included in the **existing evidence mapping** only in
strict mode as `evidence.independent_source_text_assurance` with
per-source statuses and reason codes. The confidence signal includes
`independent_source_text_unverified` (fail-closed) or
`independent_source_exact_text_observed` (all matched).

**No changes** are made to unconfigured retrieval workflows,
the external provider registry, source freshness calculations, claim
extraction, entity relevance, general conflict detection, or the legacy
Reality State JSON fields. No network retrieval is performed by this
new check unless **backend-owned code deliberately installs a reader**.

## Honest limits of assurance

- A backend callback can be broken or untrustworthy. The checker only
  validates the reader's returned text and exact URL; **its URI equality
  does not prove the reader truly fetched that publisher**.
- Exact substring matching is intentionally stricter than paraphrase
  entailment. Legitimate summaries that do not appear verbatim are
  rejected in strict mode; word substitutions, HTML presentation
  transformations, and quotes split across elements may fail.
- A malicious independent reader that simply echoes caller text could
  falsely pass every source. Do not install such a reader.
- An original publisher can publish an incorrect claim. Text presence
  does not establish factual truth, independence, or interpretation.
- A malicious page can include a false claim and its negation; presence
  is not positive semantic endorsement.
- The default application **does not configure a production independent
  publisher reader**. Strict mode therefore correctly returns
  `uncertain`. Do not claim live content verification is now deployed.
- A single matching quote with an explicit entity is necessary
  under this narrow policy but **not sufficient** for general
  factual assurance. `status="supported"` remains a structural status.
- Future reader implementation must separately address allowlisted
  origins, SSRF/DNS rebinding, redirect policies, proxy configuration,
  timeout, max response bytes, MIME parsing, TLS authentication,
  retention/capture times and operational protection. This step
  **does not expose an arbitrary URL-fetch service**.

## Correct backend integration

A trusted service operator may inject an independent reader with:
```python
from dataclasses import replace
from backend.app.orchestrator.dependencies import OrchestrationDependencies
from backend.app.reality.independent_source_text_assurance import (
    IndependentSourceTextAssurance,
)

def operator_owned_read(uri: str) -> dict[str, str]:
    # Implementation must genuinely and safely retrieve source text
    # from a separately trusted channel. Do not echo submitted inputs.
    raise NotImplementedError("Install an audited operator-owned reader")

services = replace(
    OrchestrationDependencies.default(),
    independent_source_text_assurance=IndependentSourceTextAssurance(
        operator_owned_read
    ),
)
```

Application code can then call
`build_reality_state_from_evidence(..., dependencies=services,
require_independent_source_text_match=True)`.

**Do not** treat the above placeholder as a working publisher reader.
The default HTTP route deliberately cannot take an untrusted
implementation of a reader from a public caller. For current production
API deployments the strict mode is **fail-closed unless server code
is customized to use independently verified providers**.

## Reproducible controlled measurements

Step 220 adds
`backend/app/evaluation/independent_source_assurance_benchmark.py`.
It reuses Step 218's **48 official-history-anchored controlled
scenarios**, but injects a simulated backend-owned observer that knows
the fixture's independently authored *reference summaries*, never
the attacking submitted document. This is a useful **unit/integration
benchmark for the trust boundary only**.

The fixture reference summaries are **not raw publisher page captures**
or independently blinded external ground truth. Any improved scores
demonstrate the gate *conditional on a trustworthy reader*, not real
publisher authentication or field factual accuracy. The runner also
tests a completely unconfigured backend reader, making the false-
abstention tradeoff explicit.

Historical Step 217 and 218 JSON baselines and Step 219 scorecard remain
intact. A separate Step 220 scorecard is published from actual hosted
CI output and required to match subsequent replay.

## Completion criteria

- Opt-in strict source mode is validated as a literal boolean; omitted
  callers have no behavioral change.
- The unconfigured mode fails closed with explicit source assurance
  metadata and no fake trust proof.
- A backend-owned reader can actually supply independent comparison
  text; full excerpt, URI and bounded content are checked.
- Multiple documents must **all** match, malformed or broken reader
  responses never grant support, and hashes from API clients do not
  confer authenticity.
- Existing explicit entity matching, freshness and conflict gates
  still apply; status can remain uncertain for independent reasons.
- A controlled 48-case strict-mode scorecard is saved as observed,
  including correct legitimate support and false-supported errors, with
  simulation disclosure and replay parity check.
- All backend regression tests and Step 217, 218 and 220 benchmark
  workflows pass on feature head, merged main, and final status-sync
  main SHA. **Only then** mark the engineering milestone completed.

## Product work that remains

A real operator-controlled source reader with independently captured
**original** source content; secure network fetch (or authenticated
publisher feeds), original-byte snapshots, timestamp/URI attestations,
source authenticity, separate blinded human evaluation, and semantic
support are **outside this milestone**. These should be prioritized
next, rather than claiming that the abstract reader is an active
independent fact verifier.

## Commands

```bash
python -m compileall -q backend/app
python -m pytest
python -m backend.app.evaluation.reality_state_quality_benchmark --summary-only
python -m backend.app.evaluation.official_source_quality_benchmark --summary-only
python -m backend.app.evaluation.independent_source_assurance_benchmark
```
