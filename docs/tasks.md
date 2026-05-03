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
| T0.6 | S0.3 | P0 | done | Add product-readable architecture docs | Added product vision, MVP flow, data model, and expanded architecture docs. |
| T1.1 | S1.1 | P0 | done | Add initial Pydantic memory/refactor models | Models exist in `services/memory-engine/src/memory_refactor/core/models.py`. |
| T1.2 | S1.1 | P0 | done | Add deterministic seed refactor planner | Stub exists in `core/operations.py`. |
| T1.3 | S1.2 | P0 | done | Add SQLAlchemy database session and base model | Added async session helpers, declarative base, and initial ORM records. |
| T1.4 | S1.2 | P0 | done | Add Alembic configuration and first migration | Added initial memory tables migration. |
| T1.5 | S1.2 | P0 | done | Implement memory create/list endpoints backed by Postgres | Replaced seeded `/memories` response with async DB-backed create/list handlers. |
| T1.6 | S1.3 | P0 | done | Persist refactor runs and operations | Preview endpoint now persists a run, operations, and contradictions. |
| T5.1 | S5.1 | P0 | done | Add API endpoint to start Temporal refactor workflow | `POST /refactor-runs` now accepts `raw_event_ids`, returns run/workflow identifiers, and stores a run shell. |
| T5.2 | S5.2 | P0 | done | Apply approved operations transactionally | `create_memory` operations now write canonical memory, version `1`, and `applied` state. |
| T6.1 | S6.1 | P0 | done | Fetch refactor runs from API in web app | Dashboard run list now maps `GET /refactor-runs` with sample fallback. |
| T6.2 | S6.2 | P0 | done | Fetch operation detail and source excerpts from API | Selected run operations now map from `RefactorPlan.operations` with source excerpts. |
| T6.3 | S6.3 | P0 | done | Wire approve/reject buttons to API | Review decisions persist on memory operations. |
| T2.1 | S2.1 | P0 | done | Add raw memory event model and endpoint | Added append-only raw event contract, table, repository, and API route. |
| T2.2 | S2.1 | P0 | done | Add manual raw memory batch ingestion flow | `POST /raw-memory-events/manual-batches` creates raw events and starts a refactor run. |
| T3.1 | S3.1 | P1 | done | Add pgvector embedding persistence | Added typed embedding contracts, `memory_embeddings`, and Postgres nearest-neighbor repository. |
| T3.2 | S3.2 | P1 | done | Add Postgres relationship table for graph-like MVP | Added temporal relationship contract, table, and Postgres memory graph repository. |
| T4.1 | S4.2 | P1 | done | Add Pydantic AI agent wrapper behind `RefactorAgent` port | Added optional Pydantic AI wrapper with deterministic fallback. |
| T7.1 | S7.1 | P1 | done | Add trace ID fields to refactor runs | API now returns nullable workflow and trace metadata. |
| T7.2 | S7.2 | P2 | done | Store review decisions for eval data | Review endpoint now appends decision records with optional reasons. |
| T8.1 | S8.1 | P2 | deferred | Add Qdrant adapter | Wait for retrieval scale or benchmark need. |
| T8.2 | S8.2 | P2 | deferred | Add NATS event publisher adapter | Wait for cross-service event complexity. |
| T9.1 | S9.1 | P0 | done | Add testing strategy document | Created `docs/testing-strategy.md`. |
| T9.2 | S9.2 | P0 | done | Add backend pytest unit/integration harness | Added markers, unit command, integration command, and repository tests. |
| T9.3 | S9.3 | P0 | done | Add frontend component and E2E test harness | Added Vitest, Testing Library, Playwright config, and smoke tests. |
| T9.4 | S9.4 | P1 | done | Add CI quality gate | GitHub Actions runs the default gate plus a Postgres-backed integration job. |
| T0.4 | S0.2 | P0 | done | Add repo-specific workflow skills | Added DB, API contract, UI, test gate, memory operation, and ship-change skills. |
| T0.5 | S0.2 | P0 | done | Add read-only repo reviewer agents | Added DB, UI, test gate, and architecture reviewer agents. |

## Current Next Slice

Recommended next implementation task: none in the non-deferred queue.

Reason: the main product-loop persistence, retrieval, agent fallback, review, apply, eval-data scaffolding, and CI gates are now in place. The only remaining tracked tasks are deferred scale-out adapters (`T8.1` Qdrant and `T8.2` NATS) that should wait for concrete scale or cross-service event needs.

## Recently Completed

- `T0.1`: Monorepo scaffold.
- `T0.2`: Codex operating context.
- `T0.3`: Epics, stories, and tasks docs.
- `T0.6`: Product vision, MVP flow, data model, and expanded architecture docs.
- `T1.1`: Initial memory contracts.
- `T1.2`: Deterministic planner stub.
- `T1.3`: SQLAlchemy database base and session helpers.
- `T1.4`: Alembic configuration and first migration.
- `T1.5`: Database-backed memory create/list endpoints.
- `T1.6`: Refactor preview persistence with run/operation repository and API list/detail endpoints.
- `T5.1`: Temporal workflow start endpoint with typed raw-event input and persisted workflow output path.
- `T5.2`: Transactional apply endpoint for approved `create_memory` operations with immutable version write.
- `T6.1`: API-backed refactor run list in the web dashboard.
- `T6.2`: API-backed operation detail and source excerpt rendering.
- `T6.3`: API-backed approve/reject review state for Memory PR operations.
- `T2.1`: Raw memory event contract, persistence, API, and refactor-run evidence wiring.
- `T2.2`: Manual pasted-memory batch endpoint that creates raw events and starts a refactor run.
- `T3.1`: pgvector-backed memory embedding persistence and nearest-neighbor retrieval adapter.
- `T3.2`: Postgres-backed temporal relationship persistence and retrieval adapter.
- `T4.1`: Pydantic AI refactor agent wrapper with deterministic fallback and source-grounding checks.
- `T7.1`: Refactor run workflow and trace metadata exposed through backend and web API contracts.
- `T7.2`: Review decisions persisted with optional reasons for future eval exports.
- `T9.1`: Testing strategy.
- `T9.2`: Backend test harness.
- `T9.3`: Frontend test harness.
- `T9.4`: GitHub Actions CI quality gate for default checks.
- `T0.4`: Repo-specific workflow skills.
- `T0.5`: Read-only reviewer agents.
