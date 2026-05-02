# Tasks

This file tracks implementation-level work. Keep tasks small enough to complete in one focused session.

Status legend:

- `todo`
- `in-progress`
- `done`
- `blocked`
- `deferred`

Priority legend:

- `P0`: needed for the next working product loop
- `P1`: important soon
- `P2`: useful later

## Active Task Queue

| ID | Story | Priority | Status | Task | Notes |
| --- | --- | --- | --- | --- | --- |
| T0.1 | S0.1 | P0 | done | Create monorepo scaffold | Added web, memory-engine, infra, docs. |
| T0.2 | S0.2 | P0 | done | Add repo-local Codex operating context | Added `AGENTS.md`, context docs, and baseline skills. |
| T0.3 | S0.3 | P0 | done | Add epics, stories, and task tracking docs | Created `docs/epics.md`, `docs/stories.md`, and `docs/tasks.md`. |
| T1.1 | S1.1 | P0 | done | Add initial Pydantic memory/refactor models | Models exist in `services/memory-engine/src/memory_refactor/core/models.py`. |
| T1.2 | S1.1 | P0 | done | Add deterministic seed refactor planner | Stub exists in `core/operations.py`. |
| T1.3 | S1.2 | P0 | done | Add SQLAlchemy database session and base model | Added async session helpers, declarative base, and initial ORM records. |
| T1.4 | S1.2 | P0 | done | Add Alembic configuration and first migration | Added initial memory tables migration. |
| T1.5 | S1.2 | P0 | done | Implement memory create/list endpoints backed by Postgres | Replaced seeded `/memories` response with async DB-backed create/list handlers. |
| T1.6 | S1.3 | P0 | todo | Persist refactor runs and operations | Preview endpoint should create a run record. |
| T5.1 | S5.1 | P0 | todo | Add API endpoint to start Temporal refactor workflow | Should return run/workflow identifiers. |
| T6.1 | S6.1 | P0 | todo | Fetch refactor runs from API in web app | Replace sample run data. |
| T6.2 | S6.2 | P0 | todo | Fetch operation detail and source excerpts from API | Replace sample operation data. |
| T6.3 | S6.3 | P0 | todo | Wire approve/reject buttons to API | Keep local optimistic state simple. |
| T2.1 | S2.1 | P1 | todo | Add raw memory event model and endpoint | Required for real ingestion. |
| T3.1 | S3.1 | P1 | todo | Add pgvector embedding persistence | Start with adapter interface plus Postgres implementation. |
| T3.2 | S3.2 | P1 | todo | Add Postgres relationship table for graph-like MVP | Include temporal validity fields. |
| T4.1 | S4.2 | P1 | todo | Add Pydantic AI agent wrapper behind `RefactorAgent` port | Keep deterministic stub as fallback. |
| T7.1 | S7.1 | P1 | todo | Add trace ID fields to refactor runs | Integration can be no-op locally. |
| T7.2 | S7.2 | P2 | todo | Store review decisions for eval data | Useful after review UI is real. |
| T8.1 | S8.1 | P2 | deferred | Add Qdrant adapter | Wait for retrieval scale or benchmark need. |
| T8.2 | S8.2 | P2 | deferred | Add NATS event publisher adapter | Wait for cross-service event complexity. |

## Current Next Slice

Recommended next implementation task: `T1.6`.

Reason: memory units can now be created and listed through the database-backed API. The next blocker is persisting refactor runs and operations so Memory PRs are not transient planner output.

## Recently Completed

- `T0.1`: Monorepo scaffold.
- `T0.2`: Codex operating context.
- `T0.3`: Epics, stories, and tasks docs.
- `T1.1`: Initial memory contracts.
- `T1.2`: Deterministic planner stub.
- `T1.3`: SQLAlchemy database base and session helpers.
- `T1.4`: Alembic configuration and first migration.
- `T1.5`: Database-backed memory create/list endpoints.
