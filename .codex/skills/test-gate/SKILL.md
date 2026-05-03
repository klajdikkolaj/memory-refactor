---
name: test-gate
description: Use before finishing a change to decide and run the right unit, integration, E2E, and structure checks for this repo.
---

# Test Gate

## Goal

Pick the smallest sufficient validation set for the change and avoid calling work complete with missing evidence.

## Start Here

- Read `docs/testing-strategy.md`.
- Check `git status --short`.
- Inspect `git diff --stat`.

## Test Selection

- Structural/docs/scaffold change: `make check-structure`.
- Python domain-only change: `make test-python-unit`.
- Python persistence/API change: `make test-python-unit` and `make test-python-integration`.
- Web type/component change: `make check-web` and `make test-web-unit`.
- Web flow change: add `make test-web-e2e`.
- Compose/infra change: `docker compose config`.
- Pre-review gate: run all relevant checks from the rows above.

## Workflow

1. Map changed files to test layers.
   Success criteria: Each changed surface has a validation target.
2. Run checks or identify setup blockers.
   Success criteria: Failures are concrete and reproducible.
3. Fix test-environment issues when reasonable.
   Success criteria: Tooling problems do not remain unexplained.
4. Summarize evidence.
   Success criteria: Final answer names checks run and remaining risks.

## Rules

- Do not run integration tests silently without Docker/Postgres context.
- Do not claim UI completion without browser verification when feasible.
- Do not let passing unit tests substitute for migration or E2E validation when those surfaces changed.
