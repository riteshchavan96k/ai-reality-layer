# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 35 — Reality Context Requirement Detection — implementation and validation coverage complete.

### Step 35 Scope

- Tasks are deterministically classified for whether current-world information is required.
- Tasks can explicitly request external evidence through source, citation, official, and related signals.
- Current-information requests automatically require external evidence.
- Temporal scope is explicitly represented for current-information requests.
- Reality-context requirements are attached to task analysis so downstream routing and execution layers can consume them.
- Existing execution, evaluation, recovery, budget, approval, and trace behavior remains intact.
- Signal matching is word-aware to avoid accidental substring matches.

### Step 35 Design Boundary

This step establishes the decision point for the Reality Layer: determining when external or current-world context is needed before reasoning or acting. It does not fetch the web, implement RAG, claim factual correctness, or introduce ML training. Those capabilities can build on this contract in later steps.
