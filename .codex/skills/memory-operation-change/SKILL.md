---
name: memory-operation-change
description: Use when changing MemoryUnit, MemoryOperation, RefactorPlan, contradiction, versioning, review, or apply semantics.
---

# Memory Operation Change

## Goal

Protect the product's core primitive: typed, reviewable, source-grounded memory operations.

## Start Here

- Read `docs/architecture.md`.
- Read `docs/codex-context.md`.
- Inspect `services/memory-engine/src/memory_refactor/core/models.py`.
- Inspect `services/memory-engine/src/memory_refactor/core/operations.py`.
- Check related persistence tables and API routes if the change crosses storage or UI.

## Invariants

- Agents propose operations; they do not directly mutate canonical memory.
- Approved operations must be auditable and rollback-aware.
- Every operation should carry rationale, confidence, source memory IDs, and review requirements.
- Contradictions must remain reviewable rather than being silently resolved.
- Postgres is the source of truth; vector and graph layers are derived.

## Workflow

1. Identify the operation invariant affected.
   Success criteria: The semantic change is explicit.
2. Update typed contracts first.
   Success criteria: Pydantic and TypeScript contracts stay aligned where needed.
3. Update persistence and workflows only after contract shape is clear.
   Success criteria: Storage and Temporal code preserve review/apply boundaries.
4. Add tests.
   Success criteria: Unit tests cover contract behavior; integration tests cover persistence if touched.
5. Run validation.
   Success criteria: Relevant backend, frontend, and workflow checks are complete or blocked explicitly.

## Output

Return:

- Operation semantics changed.
- Invariants preserved.
- Tests and checks run.
- Any unresolved product decision.
