# Memory Refactor

AI-native memory refactor engine built as a product monorepo.

The intended stack is:

- `apps/web`: Next.js, React, TypeScript, Tailwind, shadcn-style UI primitives.
- `services/memory-engine`: FastAPI, Pydantic, Pydantic AI-ready contracts, Temporal worker.
- `infra`: Docker Compose for Postgres with pgvector and Temporal.
- `docs`: durable architecture, product, and Codex context.

## First Slice

This scaffold starts with the lean version:

- Next.js dashboard shell for memory PR review.
- Python memory engine with typed memory/refactor models.
- Temporal workflow and activity placeholders.
- Postgres/pgvector as the source-of-truth and semantic retrieval base.
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
cd services/memory-engine && uv sync --extra dev
```

## Local Services

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Temporal UI: `http://localhost:8088`
- Postgres: `localhost:5432`

## Product Principle

Build a durable memory compiler, not a summarizer. The important primitive is a typed, reviewable memory operation that can be traced, retried, audited, and rolled back.

## Tests

```sh
make test-python-unit
make test-python-integration
make check-web
make test-web-unit
make test-web-e2e
```

Backend integration tests require Postgres from Docker Compose. See `docs/testing-strategy.md` for the full test matrix.
