# AI Reality Layer

## Project Status

Initial development.

## Vision

AI Reality Layer is an experimental infrastructure project exploring how AI systems can establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Current Stage

Step 32 — Persistent Outcome Memory — implementation and validation coverage complete.

### Step 32 Scope

- Execution outcomes can now be stored in a persistent SQLite-backed memory store.
- Persistent storage preserves the structured outcome interface used by routing optimization.
- Raw task text is never persisted; only a SHA-256 task fingerprint is stored.
- Persisted outcomes survive process restarts and remain available for historical routing signals.
- Aggregate statistics and task-type-specific routing signals are available from persistent records.
- The existing in-memory memory remains available for isolated tests and lightweight use.
- Persistence is opt-in through the `ARL_OUTCOME_MEMORY_PATH` environment variable, preserving backward compatibility.
- Local SQLite runtime state is excluded from version control.
- Automated tests cover persistence across instances, privacy of stored task data, task-type isolation, statistics, recent-record ordering, and configuration validation.

### Step 32 Design Boundary

SQLite is the first durable storage implementation for local development and the MVP foundation. A PostgreSQL-backed implementation can replace or complement it later when deployment scale and concurrency requirements justify it.
