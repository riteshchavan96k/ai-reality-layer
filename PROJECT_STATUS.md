# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 33 — Evaluation Intelligence — implementation and validation coverage complete.

### Step 33 Scope

- Response evaluation now includes a reference-free task-response relevance signal.
- Relevance is calculated deterministically from normalized task and response terms.
- Structural integrity and relevance are combined into a single evaluation score.
- Low relevance or incomplete execution evidence produces an explicit review state.
- Evaluation exposes matched terms and coverage signals for observability and future routing optimization.
- The evaluator does not claim factual or semantic correctness; it is a reference-free relevance foundation.
- Existing orchestration, benchmarking, retry, fallback, budget, trace, and outcome-memory behavior remains compatible.
- Automated tests cover strong overlap, low overlap, case normalization, empty responses, evaluator integration, and review behavior.

### Step 33 Design Boundary

This step deliberately avoids model-based judging, external reference answers, or ML training. Those can be added later when the system has suitable evaluation data and task-specific quality criteria.
