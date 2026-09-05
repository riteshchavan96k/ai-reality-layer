# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 34 — Evaluation-Guided Recovery — implementation and validation coverage complete.

### Step 34 Scope

- Model execution is evaluated immediately after a successful initial execution.
- A response in review state can trigger deterministic recovery using alternative routed candidates.
- Recovery reuses the existing retry policy and shared execution budget.
- Each recovery candidate is evaluated with the same structural and reference-free relevance evaluator.
- The highest-scoring response is retained; recovery stops early when a passing evaluation is found.
- Recovery metadata exposes whether recovery was used, candidates tried, attempts consumed, improvement, final model, and final score.
- Human approval still occurs before any execution or recovery attempt.
- Failed recovery candidates do not replace the current best successful response.

### Step 34 Design Boundary

This step adds an evaluation-guided execution loop without claiming factual or semantic correctness. It does not introduce model-based judging, automatic task rewriting, response synthesis, or ML training. Those remain future extensions when stronger evaluation signals and suitable data are available.
