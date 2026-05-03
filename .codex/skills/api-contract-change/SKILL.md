---
name: api-contract-change
description: Use when changing FastAPI routes, Pydantic request/response models, OpenAPI contracts, or frontend-facing API behavior.
---

# API Contract Change

## Goal

Keep API contracts typed, explicit, and stable enough for the Next.js app and future SDK/API consumers.

## Start Here

- Read `docs/codex-context.md`.
- Inspect `services/memory-engine/src/memory_refactor/core/models.py`.
- Inspect affected route modules under `services/memory-engine/src/memory_refactor/api/routes`.
- Check whether the web app has matching types in `apps/web/lib`.

## Workflow

1. Separate public API models from persistence details when needed.
   Success criteria: Public responses do not leak internal-only fields.
2. Keep write contracts strict.
   Success criteria: Pydantic models reject unknown fields where correctness matters.
3. Route through domain/repository functions.
   Success criteria: Route handlers remain thin orchestration layers.
4. Update frontend contracts if the UI consumes the endpoint.
   Success criteria: TypeScript types or API client code match the Python response.
5. Run validation.
   Success criteria: `make test-python-unit`; add integration tests for persistence-backed endpoints; run web checks if frontend types changed.

## Rules

- Use `response_model` on FastAPI endpoints.
- Prefer typed request models over `dict` or `Any`.
- Avoid breaking endpoint shape without updating docs/tasks and frontend callers.
- Keep model-provider and Temporal details out of public responses unless explicitly needed.

## Output

Return:

- Endpoint or contract changed.
- Backward-compatibility notes.
- Frontend impact.
- Tests and checks run.
