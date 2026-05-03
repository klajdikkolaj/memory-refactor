# Product Vision

## Short Version

Memory Refactor is self-cleaning memory infrastructure for AI applications.

Most AI memory systems append raw messages forever, retrieve with embeddings, and hope the context is still useful. This product treats memory like a codebase:

```txt
raw messages -> raw memory events -> refactor agent -> Memory PR -> clean memory units -> retrieval API
```

The goal is not to build another summarizer. The goal is to build a durable memory compiler that maintains long-term knowledge with evidence, typed operations, review, version history, and rollback.

## Product Metaphor

```txt
Raw chats and imports       = messy commits
Raw memory events           = append-only evidence log
Refactor agent              = senior engineer proposing a cleanup
Memory operations           = typed mutations
Memory PR                   = reviewable change set
Structured memory store     = production knowledge base
Memory versions             = audit and rollback history
Retrieval API               = clean context for downstream agents
```

This is the core distinction:

```txt
Vector databases retrieve memory.
Memory Refactor maintains memory.
```

## What The Product Should Achieve

Memory Refactor should turn messy user or organization history into durable, useful memory:

- stable facts
- preferences
- goals
- projects
- relationships
- decisions
- constraints
- open questions
- contradictions
- source-grounded summaries

The product should help users see:

- what changed
- why it changed
- which raw events support the change
- which memories were merged, archived, superseded, or marked conflicted
- whether the change needs human review
- how to undo or inspect the history later

## Core Principles

### Raw Evidence Is Preserved

Raw memory events are append-only evidence. They are not the normal retrieval surface, but they must remain available for audit, debugging, and rollback.

### Clean Memory Is Retrieved

Downstream AI agents should retrieve clean memory units, not old raw chats by default. Raw events can be inspected when the system needs evidence.

### Agents Propose, The Backend Applies

The refactor agent must produce schema-valid operations. It does not directly mutate canonical memory.

Every operation should include:

- operation kind
- rationale
- confidence
- source memory IDs when existing memories are affected
- source event IDs when raw events justify the change
- review state

### No Source, No Memory

A new or updated memory must be grounded in source evidence. Unsupported claims should be rejected, lowered in confidence, or converted into an open question.

### Archive Or Supersede Instead Of Hard Delete

Memory should behave like history-aware code. Old facts can become archived, stale, superseded, or conflicted, but they should not disappear silently.

### Contradictions Stay Reviewable

The system should not fake certainty when facts conflict. It should distinguish:

- true contradiction
- user preference shift
- older fact superseded by newer fact
- context-specific difference
- insufficient evidence

## MVP Product Loop

The first useful product slice is:

1. User pastes messy memory text.
2. API stores it as raw memory events.
3. User starts a refactor run.
4. Temporal executes a durable workflow.
5. Refactor logic produces a typed `RefactorPlan`.
6. The plan is persisted as a Memory PR.
7. User reviews operations and sources.
8. Approved operations update clean memory transactionally.
9. Retrieval returns clean memory only.

That proves the product before adding heavier infrastructure.

## MVP Boundary

Build first:

- Next.js product UI
- FastAPI memory engine
- Pydantic contracts
- Temporal workflow boundary
- Postgres as source of truth
- pgvector as the first semantic retrieval layer

Defer until the core loop proves the need:

- Qdrant
- Graphiti or Neo4j-style graph storage
- NATS JetStream
- LiteLLM proxy
- Langfuse and full OpenTelemetry wiring
- R2/S3 archives
- Kubernetes

Those systems should be introduced behind ports and adapters, not treated as required day-one runtime dependencies.

## Positioning

Strong product names and framing:

- Memory refactoring for AI agents.
- Self-cleaning memory infrastructure.
- A knowledge store that cleans itself.
- Memory PRs for long-term AI context.

The developer-facing pitch:

> Your AI app has memory. But who maintains it?

The technical pitch:

> Controlled mutation with diffs, evidence, confidence, review, and rollback.

## Non-Goals For The First Slice

Do not start with:

- email integrations
- browser extensions
- billing
- multi-tenant enterprise permissions
- dedicated vector clusters
- graph database operations
- event-stream choreography
- Kubernetes production topology

The first slice should make one thing obvious: messy memory becomes clean, reviewable, source-grounded memory.
