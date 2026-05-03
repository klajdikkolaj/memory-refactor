# Repository Instructions

## Structure

- `apps/web`: Next.js product UI for memory explorer, memory PRs, review queues, and settings.
- `services/memory-engine`: Python FastAPI API, typed memory contracts, AI/refactor logic, and Temporal worker.
- `infra`: local runtime infrastructure such as Postgres/pgvector and Temporal.
- `docs`: product architecture, data contracts, Codex context, and durable handoff notes.
- `.codex/skills`: repo-local Codex workflows.
- `.codex/agents`: read-only specialist reviewers for database, UI, test gate, and architecture synthesis.

## Commands

- Structure check: `make check-structure`
- Local infra: `make infra-up`
- API dev: `make dev-api`
- Worker dev: `make dev-worker`
- Web dev: `make dev-web`
- Python tests: `make test-python`
- Python unit tests: `make test-python-unit`
- Python integration tests: `make test-python-integration`
- Web lint/type-check: `make check-web`
- Web unit tests: `make test-web-unit`
- Web E2E tests: `make test-web-e2e`

## Working Rules

- Read `docs/codex-context.md` before architecture or cross-service changes.
- Keep the MVP boundary lean: Postgres/pgvector, FastAPI, Temporal, and Next.js first.
- Add Qdrant, NATS, Graphiti, LiteLLM, Langfuse, and object storage behind adapters before making them mandatory.
- Do not commit secrets. Use `.env.example` files for required configuration.
- Do not edit `.venv`, generated build outputs, or IDE metadata unless the user explicitly asks.
- Keep changes scoped to the requested product slice.

## Verification

- Run `make check-structure` after structural changes.
- Run `make test-python` after Python behavior changes once dependencies are installed.
- Run `make check-web` after web code changes once dependencies are installed.
- Follow `docs/testing-strategy.md` for unit, integration, workflow, and E2E test expectations.
- For UI changes, verify in a browser when the app can run locally.
- For workflow changes, verify Temporal worker startup or unit-test workflow/activity logic when feasible.

## Delegation

- Delegate read-only discovery or bounded audits when it materially improves coverage.
- Keep overlapping edits on the main thread unless file ownership is clearly disjoint.
- Require delegated work to report changed files, checks run, and residual risks.
- For multi-surface work, use `.codex/skills/repo-parallel-work/SKILL.md` to split ownership across web, API, worker, infra, docs, and verification.
- Use `.codex/agents/*.toml` for repeated read-only reviewer/advisor passes; keep implementation ownership on the main thread or clearly scoped workers.

## Done Means

- The smallest useful slice is implemented.
- Relevant checks are run or clearly called out as not run.
- Data contracts remain typed and reviewable.
- The final summary names changed files and any remaining risk.
