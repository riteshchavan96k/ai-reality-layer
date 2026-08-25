# AI Reality Layer — AI Development Instructions

## Project

This repository contains the AI Reality Layer project.

The long-term vision is to build infrastructure that helps AI systems establish evidence-backed, current representations of relevant real-world information before reasoning or acting.

## Development Principles

1. Do not make large changes without explaining the plan first.
2. Prefer small, testable changes.
3. Do not invent requirements.
4. Ask for clarification when a requirement is genuinely ambiguous.
5. Do not expose secrets, API keys, passwords, or credentials.
6. Do not add unnecessary dependencies.
7. Prefer simple architecture over premature complexity.
8. Every meaningful code change should have appropriate tests.
9. Do not claim something works without testing it.
10. Preserve existing working functionality unless a change explicitly requires modifying it.
11. Inspect the existing code before changing it.
12. Keep documentation synchronized with important architectural changes.

## Git Safety

Before significant changes:

- inspect the current Git status
- understand what files will change
- review the diff before committing

Do not rewrite Git history or delete branches unless explicitly instructed.

## AI Coding Agent Behavior

Before implementing a non-trivial request:

1. Explain your understanding.
2. Identify relevant files.
3. Propose a concise implementation plan.
4. Identify risks or assumptions.
5. Then implement only the approved scope.

After implementation:

1. Run relevant tests.
2. Report what changed.
3. Report tests performed and their results.
4. Report any remaining uncertainty.