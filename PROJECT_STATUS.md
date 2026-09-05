# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 28 — Execution Budgets and Guardrails — implementation and validation coverage complete.

### Step 28 Scope

- Total model execution attempts are bounded by an explicit execution budget.
- Retry attempts and fallback attempts share the same total budget.
- Fallback execution stops when the remaining budget is exhausted.
- Orchestration exposes total attempts and the configured budget limit.
- Existing retry behavior remains configurable per model.
- Human approval remains a gate before any execution budget is consumed.
- Automated tests cover budget accounting, validation, over-consumption, exhaustion, and fallback with remaining budget.
