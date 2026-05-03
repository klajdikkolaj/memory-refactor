# Memory Refactor

AI-native memory refactor engine built as a product monorepo.

Memory Refactor treats memory like a codebase. Raw chats, notes, imports, and API events are preserved as evidence. A refactor agent proposes typed operations. Users review those operations as Memory PRs. Approved changes become clean, source-grounded memory that downstream AI agents can retrieve.

The product goal is self-cleaning memory infrastructure for AI applications, not another summarizer.

The intended stack is:

- `apps/web`: Next.js, React, TypeScript, Tailwind, shadcn-style UI primitives.
- `services/memory-engine`: FastAPI, Pydantic, Pydantic AI-ready contracts, Temporal worker.
- `infra`: Docker Compose for Postgres, pgvector, and Temporal.
- `docs`: durable architecture, product, and Codex context.

## Product Loop

```txt
raw memory events -> durable refactor run -> Memory PR -> approved operations -> clean memory units -> retrieval API
```

The important primitive is a typed, reviewable memory operation that can be traced, retried, audited, and rolled back.

## Docs Map

- `docs/product-vision.md`: what the product is and why it exists.
- `docs/architecture.md`: service boundaries, runtime diagrams, and future adapter strategy.
- `docs/mvp-flow.md`: first working product loop and demo scenario.
- `docs/data-model.md`: canonical contracts, tables, and invariants.
- `docs/epics.md`: durable product epics.
- `docs/stories.md`: user/operator stories.
- `docs/tasks.md`: implementation queue and current next task.
- `docs/testing-strategy.md`: unit, integration, workflow, frontend, and E2E test policy.

## First Slice

This scaffold starts with the lean version:

- Next.js dashboard shell for memory PR review.
- Python memory engine with typed memory/refactor models.
- Temporal workflow and activity scaffolding for durable refactor runs.
- Postgres as the source of truth, with pgvector as the first semantic retrieval layer.
- Qdrant, NATS, LiteLLM, Langfuse, R2, and Graphiti are planned integration boundaries, not required runtime services on day one.

## Commands

```sh
make check-structure
make infra-up
make dev-api
make dev-worker
make dev-web
```

Install dependencies first when you are ready to run services:

```sh
brew install uv
corepack enable
corepack prepare pnpm@9.12.3 --activate
pnpm install
cd services/memory-engine && uv sync --extra dev --extra ai
```

## Local Services

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Temporal UI: `http://localhost:8088`
- Postgres: `localhost:5432`

## Tests

```sh
make test-python-unit
make test-python-integration
make check-web
make test-web-unit
make test-web-e2e
```

Backend integration tests require Postgres from Docker Compose. See `docs/testing-strategy.md` for the full test matrix.
