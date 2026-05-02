---
name: repo-parallel-work
description: Use when work in this repository can be split across multiple Codex subagents with clear ownership and low merge conflict risk.
---

# Repo Parallel Work

## Goal

Use subagents to reduce latency and improve review quality without creating overlapping edits.

## When To Use

Use this skill when at least one is true:

- The task spans two or more independent surfaces.
- Discovery or verification can run while the main thread implements.
- A second-pass audit would reduce risk before shipping.
- Work can be split by ownership boundary.

Do not use it for trivial single-file edits or tightly coupled design decisions.

## Ownership Boundaries

Preferred write scopes:

- Web: `apps/web/**`
- API/contracts: `services/memory-engine/src/memory_refactor/api/**` and `services/memory-engine/src/memory_refactor/core/**`
- Temporal worker: `services/memory-engine/src/memory_refactor/worker/**`
- Python tests: `services/memory-engine/tests/**`
- Infra: `compose.yaml`, `infra/**`, `.env.example`
- Docs/Codex: `AGENTS.md`, `docs/**`, `.codex/skills/**`

Avoid assigning two workers to the same boundary unless one is read-only.

## Lead Workflow

1. Decide the immediate task to do locally.
   Success criteria: The main thread is not blocked on a delegated task.
2. Delegate bounded side work.
   Success criteria: Each worker has a clear responsibility, write scope, validation target, and output format.
3. Continue with non-overlapping work.
   Success criteria: Parallelism actually saves time.
4. Integrate results.
   Success criteria: The lead resolves conflicts and preserves repo architecture.
5. Run final validation.
   Success criteria: Repo-required checks or setup blockers are reported.

## Worker Prompt Contract

Every worker assignment should include:

- Responsibility:
- Write scope:
- Validation target:
- Expected output:

Required worker report:

- Completed or blocked:
- Findings or decisions:
- Files changed:
- Checks run:
- Risks or open questions:

## Verification Pattern

Strong default splits:

- Implementation worker plus read-only verification worker.
- Architecture discovery worker plus main-thread implementation.
- Web implementation worker plus UI verification worker.

## Guardrails

- Prefer a small number of focused workers.
- Prefer read-only workers when architecture is still uncertain.
- Keep cross-boundary integration on the main thread.
- Do not use workers to bypass final repo validation.
