---
name: ship-change
description: Use when preparing this repo's current change set for review, handoff, commit, or PR.
---

# Ship Change

## Goal

Turn an in-progress change into a review-ready change set with clear validation evidence and no accidental scope.

## Start Here

- Read `AGENTS.md`.
- Read `docs/codex-handoff.md`.
- Read `docs/testing-strategy.md`.
- Run `git status --short`.
- Run `git diff --stat`.

## Workflow

1. Confirm intended scope.
   Success criteria: Dirty unrelated work is identified and excluded from summary.
2. Inspect the diff.
   Success criteria: No debug artifacts, generated caches, or accidental files are included.
3. Run the test gate.
   Success criteria: Checks match changed surfaces.
4. Update tracking docs if task status changed.
   Success criteria: `docs/tasks.md` and handoff remain truthful.
5. Produce review summary.
   Success criteria: Summary includes what changed, why, checks run, and known risks.

## Default Checks

- `make check-structure`
- `docker compose config`
- `make test-python-unit` if Python changed
- `make test-python-integration` if persistence/API storage changed
- `make check-web` if web changed
- `make test-web-unit` if components changed
- `make test-web-e2e` if browser flows changed

## Rules

- Do not stage or commit unless the user asks.
- Do not include `.venv`, `node_modules`, Playwright reports, or test caches.
- If a required check cannot run, explain the exact setup blocker.
