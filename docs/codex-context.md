# Codex Context

## What This Repo Does

Memory Refactor is an AI memory infrastructure product. It ingests raw memory events, turns them into durable memory units, proposes typed refactor operations, and lets users review memory PRs before changes become canonical.

The product should behave like an AI infrastructure system:

- typed operations instead of free-form summaries
- durable workflows instead of one-shot jobs
- Postgres as truth
- semantic and graph retrieval as derived intelligence layers
- full traceability for every model decision

## Current Architecture

- Product UI: `apps/web`
- API and memory engine: `services/memory-engine/src/memory_refactor/api`
- Core contracts: `services/memory-engine/src/memory_refactor/core`
- Temporal worker: `services/memory-engine/src/memory_refactor/worker`
- Local infrastructure: `compose.yaml` and `infra/`

## Planning Docs

- `docs/epics.md`: durable product epics and success criteria.
- `docs/stories.md`: user/operator stories grouped by epic.
- `docs/tasks.md`: implementation queue with priorities and status.

## MVP Boundary

Build first:

- Next.js dashboard shell
- FastAPI service
- Pydantic memory/refactor models
- Temporal workflow placeholders
- Postgres with pgvector extension

Defer until the core loop works:

- Qdrant
- Graphiti or dedicated graph database
- NATS JetStream
- LiteLLM proxy
- Langfuse and full OpenTelemetry wiring
- R2/S3 archives
- Kubernetes

## Important Data Contracts

- `MemoryUnit`: canonical memory fact, preference, goal, source, or observation.
- `RawMemoryEvent`: unprocessed input from conversations, imports, APIs, or archives.
- `MemoryOperation`: typed mutation such as merge, split, archive, supersede, or mark contradiction.
- `RefactorPlan`: reviewable batch of memory operations.
- `MemoryVersion`: immutable history record for rollback and audit.
- `Contradiction`: claim pair that needs model or human resolution.

## High-Risk Areas

- Memory corruption from partially applied operations.
- LLM output that is not schema-valid or not source-grounded.
- Silent overwrites of historical truth.
- Semantic retrieval drift when embeddings change.
- Graph facts without temporal validity windows.
- Untraceable model decisions or costs.

## Product Glossary

- Memory PR: a proposed set of memory changes awaiting review.
- Refactor run: one durable Temporal execution that produces a plan.
- Memory compiler: the engine that turns raw memory into typed operations and versioned facts.
- Source of truth: Postgres records and immutable versions.
- Derived layers: embeddings, graph edges, archives, traces, and caches.
