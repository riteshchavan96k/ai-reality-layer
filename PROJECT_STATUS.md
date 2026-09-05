# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 31 — Adaptive Routing Optimization — implementation and validation coverage complete.

### Step 31 Scope

- Historical outcome signals can now rank candidate models for a specific task type.
- Routing optimization uses deterministic success, evaluation, and attempt signals rather than ML training.
- Insufficient historical data is explicit and keeps the system in exploration mode.
- Task-type isolation prevents outcomes from unrelated task classes influencing a routing decision.
- Optimized candidate order is passed into existing fallback execution.
- Routing exposes optimization status, ranking signals, and exploration state for observability.
- Existing capability-based model selection remains the baseline when historical routing evidence is unavailable.
- Automated tests cover exploration, historical ranking, task-type isolation, router integration, and configuration validation.
