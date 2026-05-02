---
name: repo-workflow
description: Use when working inside this repository and you need the repo-specific workflow, validation, and safety rules.
---

# Repo Workflow

## Start Here

- Read `AGENTS.md`.
- Read `docs/codex-context.md` for product and architecture context.
- Check `git status --short`.
- Inspect the smallest relevant service before editing.

## Workflow

1. Confirm the product slice.
   Success criteria: The affected app, service, or infra boundary is clear.
2. Keep the MVP boundary intact.
   Success criteria: New systems are optional adapters unless the task explicitly promotes them to runtime dependencies.
3. Preserve typed memory contracts.
   Success criteria: LLM-facing output is represented as Pydantic models or TypeScript types.
4. Make the smallest useful change.
   Success criteria: The diff matches the requested scope and avoids unrelated refactors.
5. Run validation.
   Success criteria: `make check-structure` runs for structural changes; service-specific checks run when dependencies are installed.
6. Summarize residual risk.
   Success criteria: Any skipped runtime, browser, or dependency validation is named clearly.

## Validation Map

- Structure: `make check-structure`
- Python: `make test-python`
- Web: `make check-web`
- Infra: `docker compose config`
- UI: run the app and verify in browser when UI behavior changes.

## Safety

- Do not edit `.venv`, `.idea`, generated build outputs, or local secrets.
- Do not make Qdrant, NATS, Graphiti, LiteLLM, Langfuse, or object storage mandatory until the core loop proves the need.
- Keep Temporal workflows deterministic; push I/O into activities.
