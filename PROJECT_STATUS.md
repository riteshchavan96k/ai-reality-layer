# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 30 — Outcome Analytics and Routing Signals — implementation and validation coverage complete.

### Step 30 Scope

- Outcome memory now exposes aggregate execution signals without storing raw task text.
- Overall success rate, average evaluation score, average attempts, and fallback rate are available.
- Per-model execution counts, success rates, average scores, and average attempts are available.
- Failed executions remain part of the analytics so reliability is measurable, not hidden.
- Empty-memory analytics return safe defaults.
- The analytics layer is descriptive only; it does not automatically change routing decisions yet.
- Automated tests cover empty statistics, aggregate signals, per-model routing signals, and raw-task-text isolation.
