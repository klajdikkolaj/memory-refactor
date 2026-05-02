---
name: repo-next-task
description: Use when the next work slice is underspecified and you need to pick the smallest meaningful next task in this repository.
---

# Repo Next Task

## Goal

Choose the next smallest meaningful slice that advances the memory refactor product without overbuilding.

## Workflow

1. Inspect current repo state and dirty work.
   Success criteria: Existing changes are understood and not overwritten.
2. Read `docs/tasks.md`.
   Success criteria: Current priorities and in-flight work are understood.
3. Identify the next product-loop gap.
   Success criteria: The gap maps to ingest, retrieve, refactor, review, apply, or observe.
4. Prefer the earliest unproven loop.
   Success criteria: The selected task makes the core memory PR flow more real.
5. Avoid premature infrastructure.
   Success criteria: Future stack pieces stay behind interfaces until the MVP needs them.

## Default Priority

1. Typed memory and operation contracts.
2. Persistence for memories and refactor runs.
3. API endpoints needed by the dashboard.
4. Temporal workflow execution.
5. Review/apply UX in the web app.
6. Observability, model routing, graph, vector scale, and event streaming.
