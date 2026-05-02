# Codex Skill Map

Use this map to choose the right Codex workflow for this repo.

## Setup And Structure

- `codex-repo-first-pass`: umbrella workflow for first serious repo setup. This repo now uses the Standard model: `AGENTS.md`, durable context docs, and repo-local skills.
- `repo-bootstrap` / `codex-repo-foundation`: narrower foundation helpers. They are useful when tightening the scaffold, but `codex-repo-first-pass` is the better entry point for a new product repo.

## Parallel Work

- `codex-parallel-repo-work`: use when a task can be split safely across web, API, Temporal worker, infra, docs, or verification.
- Repo-local version: `.codex/skills/repo-parallel-work/SKILL.md`.

Good splits:

- Web dashboard work in `apps/web`.
- API and contracts in `services/memory-engine/src/memory_refactor/api` and `core`.
- Temporal workflow work in `services/memory-engine/src/memory_refactor/worker`.
- Infra work in `compose.yaml` and `infra`.
- Read-only verification or review.

## Runtime And UI Verification

- `debug-runtime`: use after a local app, worker, API, or Compose service fails to start or behaves incorrectly.
- `verify-ui`: use after web UI changes. Browser verification is required when dependencies and runtime are available.

## Research And Architecture Decisions

- `research-to-decision`: use when outside information is needed to make a repo-grounded technical decision. Prefer official sources and end with a concrete recommendation.
- `claude-code-patterns`: use as a reference for agent-system patterns worth adapting, especially layered memory, bounded agents, deferred capabilities, and verification/advisor passes. Do not recreate a full agent runtime unless the product needs it.

## Shipping

- `ship-pr`: use before review or merge. It should inspect the diff, run repo-required checks, verify UI/runtime surfaces touched by the change, and produce a PR-ready summary.
