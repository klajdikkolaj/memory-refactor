# Architecture

## North Star

The durable primitive is a typed memory operation. Agents should propose operations, not mutate memory directly.

```txt
raw events -> memory units -> refactor plan -> memory PR -> approved operations -> versions
```

## Service Map

```txt
apps/web
  Next.js dashboard and review UI

services/memory-engine
  FastAPI API
  Pydantic contracts
  Temporal workflows and activities
  AI/refactor logic

infra
  Postgres + pgvector
  Temporal
  optional future services behind profiles
```

## MVP Runtime

```txt
Next.js -> FastAPI -> Postgres
                 |
                 v
              Temporal -> worker activities
```

Postgres stores canonical memory state. pgvector starts as the semantic retrieval layer. Temporal owns long-running refactor jobs and retries.

## Future Runtime

```txt
FastAPI
  -> LiteLLM for model routing
  -> Langfuse/OpenTelemetry for traces
  -> R2/S3 for raw archives and snapshots
  -> Qdrant for high-scale semantic retrieval
  -> Graphiti/Neo4j-style graph for temporal relationships
  -> NATS JetStream for event streams
```

Future systems should be introduced through ports/adapters so the MVP does not depend on them before the memory PR loop is proven.

## Core Product Loop

1. Ingest raw memory event.
2. Normalize into a candidate memory unit.
3. Retrieve related memories by source, semantic similarity, and relationships.
4. Ask the refactor agent for a schema-valid `RefactorPlan`.
5. Persist the plan as a Memory PR.
6. Let the user approve, reject, or edit operations.
7. Apply approved operations transactionally.
8. Write immutable versions and trace metadata.

## First Data Model

- `raw_memory_events`
- `memory_units`
- `memory_versions`
- `memory_operations`
- `refactor_runs`
- `contradictions`
- `memory_sources`
- `audit_logs`

The Python Pydantic models in `services/memory-engine/src/memory_refactor/core/models.py` are the first contract source. Database migrations should follow those contracts as implementation matures.
