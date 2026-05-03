---
name: db-change
description: Use when changing database schema, SQLAlchemy models, Alembic migrations, repositories, or persistence tests in this repo.
---

# DB Change

## Goal

Change persistence safely while keeping Postgres as the source of truth and derived systems optional.

## Start Here

- Read `docs/codex-context.md`.
- Read `docs/testing-strategy.md`.
- Inspect `services/memory-engine/src/memory_refactor/db/**`.
- Inspect current Alembic versions in `services/memory-engine/alembic/versions`.
- Check `docs/tasks.md` for the active persistence task.

## Workflow

1. Identify the contract being persisted.
   Success criteria: The Pydantic model, ORM record, and migration target are named.
2. Update schema through Alembic.
   Success criteria: Migration is reversible and matches SQLAlchemy metadata.
3. Keep repository access behind repository modules.
   Success criteria: FastAPI route handlers do not embed SQLAlchemy query logic.
4. Add or update tests.
   Success criteria: Unit mapping tests run without Postgres; integration tests are marked with `integration`.
5. Run validation.
   Success criteria: `make test-python-unit` passes; `make test-python-integration` runs for schema/repository changes when Docker is available.

## Rules

- Do not bypass Alembic for durable schema changes.
- Do not make Qdrant, Graphiti, or object storage mandatory from persistence code.
- Keep JSON columns for early flexible payloads only when the stable schema is not known yet.
- Preserve immutable version history for approved memory changes.
- Treat rollback and partial-apply failure modes as first-class design constraints.

## Output

Return:

- Schema or repository change made.
- Migration added or updated.
- Tests added or updated.
- Checks run.
- Any migration or data-loss risk.
