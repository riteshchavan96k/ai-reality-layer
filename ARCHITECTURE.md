# AI Reality Layer — Technical Architecture

## 1. Architecture Goal

Build a modular, extensible architecture for an AI Reality Layer MVP that converts retrieved information into structured, evidence-backed reality states.

## 2. Initial Architecture

AI Application / Agent
→ FastAPI
→ Query Processor
→ Retrieval Engine
→ Source Layer
→ Claim Engine
→ Evidence Engine
→ Provenance
→ Freshness
→ Conflict Detection
→ Confidence
→ Reality State
→ JSON Response

## 3. Backend

Language:

Python

API framework:

FastAPI

Initial deployment model:

Modular monolith

## 4. Core Components

### API Layer

Receives requests and returns structured responses.

### Query Processor

Understands the user's research question and identifies relevant entities, intent, and temporal requirements.

### Retrieval Engine

Retrieves relevant information from permitted external sources.

### Source Layer

Stores source metadata, including source reference, publication time, retrieval time, and source type.

### Claim Engine

Extracts structured claims from retrieved information.

### Evidence Engine

Connects claims to supporting or contradicting evidence.

### Provenance Layer

Maintains traceability between claims, evidence, and sources.

### Freshness Engine

Tracks and evaluates temporal information.

### Conflict Engine

Detects conflicting claims or evidence.

### Confidence Engine

Produces an assessment of evidence support.

### Reality State Engine

Combines claims, evidence, provenance, freshness, conflicts, and confidence into a structured reality state.

## 5. Database

Initial database:

PostgreSQL

Potential core entities:

- Entity
- Claim
- Evidence
- Source
- Conflict
- RealityState

## 6. AI Models

LLMs will be treated as replaceable components rather than being tightly coupled to the core system.

Potential tasks:

- query understanding
- claim extraction
- classification
- conflict analysis
- reasoning

A model abstraction layer may later allow multiple model providers.

## 7. Initial API Concept

POST /v1/reality

Input:

A research query or entity.

Output:

A structured reality state.

## 8. Initial Project Structure

app/
├── main.py
├── api/
├── core/
├── models/
├── services/
│   ├── retrieval/
│   ├── claims/
│   ├── evidence/
│   ├── provenance/
│   ├── freshness/
│   ├── conflicts/
│   ├── confidence/
│   └── reality/
└── db/

tests/
scripts/
docs/

## 9. Architecture Principle

Start as a modular monolith.

Do not introduce unnecessary distributed infrastructure until actual scale or product requirements justify it.

## 10. Scalability Direction

The architecture should allow future extraction of components such as:

- retrieval service
- model router
- continuous monitoring
- enterprise connectors
- specialized industry engines

without requiring a complete rewrite.

## 11. Security

Security requirements will increase when external users and enterprise customers are introduced.

Initial development will prioritize safe API boundaries, configuration through environment variables, and avoiding hard-coded secrets.

## 12. Status

Initial technical architecture defined.

Detailed implementation and database schema will be designed in subsequent steps.