# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 26 — Fallback Model Execution — implementation and validation coverage complete.

### Step 26 Scope

- Ordered fallback execution across available model candidates.
- Selected model remains the primary execution target.
- Failed primary models can fall back to the next candidate.
- Each candidate uses the existing retry policy before fallback continues.
- Execution metadata records the model used, attempts, and whether fallback occurred.
- Evaluation runs against the model that actually produced the successful result.
- Human approval remains a gate before any model execution.
- Automated tests cover primary success, fallback success, missing models, total failure, and approval gating.
