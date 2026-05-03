# Data Model

## Source Of Truth

Postgres is the source of truth. pgvector, graph relationships, object archives, traces, and caches are derived or optional layers.

The Pydantic models in `services/memory-engine/src/memory_refactor/core/models.py` define the domain semantics first. Database tables, API payloads, workflow inputs, and UI contracts should follow those models.

## Current Core Contracts

### RawMemoryEvent

Purpose: append-only evidence from chats, notes, documents, imports, APIs, or manual input.

Current fields:

- `id`
- `source_type`
- `source_id`
- `content`
- `metadata`
- `created_at`
- `processed_at`

Rules:

- Raw events are evidence, not clean memory.
- `processed_at` means the event has entered a durable plan path.
- Raw events should not be hard-deleted as part of ordinary memory cleanup.

### MemoryUnit

Purpose: canonical clean memory used for retrieval and downstream AI context.

Current fields:

- `id`
- `kind`
- `content`
- `confidence`
- `status`
- `sources`
- `metadata`
- `created_at`
- `updated_at`

Current statuses:

- `active`
- `superseded`
- `archived`
- `conflicted`

Current kinds:

- `profile`
- `fact`
- `preference`
- `goal`
- `project`
- `skill`
- `relationship`
- `decision`
- `habit`
- `constraint`
- `open_question`
- `contradiction`
- `summary`
- `observation`

Planned extensions:

- title
- importance
- explicit version number on the active row
- validity windows such as `valid_from` and `valid_until`
- stale and review lifecycle states

### MemorySource

Purpose: connect a clean memory back to evidence.

Current fields:

- `source_type`
- `source_id`
- `raw_event_id`
- `excerpt`
- `url`
- `captured_at`

Rules:

- Clean memories should cite source evidence.
- New or updated memories without source evidence should fail validation or require review.

### MemoryOperation

Purpose: typed mutation proposed by the refactor agent.

Current fields:

- `id`
- `operation`
- `source_memory_ids`
- `source_event_ids`
- `proposed_memory`
- `rationale`
- `confidence`
- `requires_human_review`
- `metadata`

Current operation kinds:

- `create_memory`
- `merge_memories`
- `split_memory`
- `supersede_memory`
- `archive_memory`
- `mark_contradiction`

Rules:

- Agents propose operations; they do not mutate canonical memory.
- Every operation needs a rationale and confidence.
- Operations that affect raw evidence should include `source_event_ids`.
- Operations that affect existing memories should include `source_memory_ids`.
- Review state belongs to the persisted operation record.

### RefactorPlan

Purpose: reviewable batch of operations produced by one refactor run.

Current fields:

- `id`
- `run_id`
- `workflow_id`
- `trace_id`
- `status`
- `summary`
- `input_event_ids`
- `operations`
- `contradictions`
- `created_at`

Rules:

- A plan is the Memory PR payload.
- A plan should be persisted before raw events are considered processed.
- Failed or invalid plans should not mutate canonical memory.
- Trace metadata may be null locally when instrumentation is disabled.

### Contradiction

Purpose: unresolved conflict that needs review or careful resolution.

Current fields:

- `id`
- `memory_ids`
- `summary`
- `confidence`
- `proposed_resolution`

Rules:

- Contradictions should remain reviewable.
- The system should avoid silently resolving ambiguous conflicts.
- Some apparent contradictions are supersessions or context-specific differences.

### MemoryVersion

Purpose: immutable history for audit and rollback.

Current fields:

- `id`
- `memory_id`
- `version`
- `snapshot`
- `operation_id`
- `created_at`

Rules:

- Approved apply should write a version record.
- Version history is required before rollback can be trusted.

### MemoryEmbedding

Purpose: derived vector representation of clean memory for semantic retrieval.

Current fields:

- `id`
- `memory_id`
- `embedding_model`
- `vector`
- `content_hash`
- `created_at`
- `updated_at`

Rules:

- Embeddings are derived from canonical memory and can be rebuilt.
- Search callers should provide explicit query vectors; model/provider integration stays behind a later agent or model gateway adapter.
- Results should preserve the embedding model used for distance ranking.

### MemoryRelationship

Purpose: derived graph-like fact edge for relationship-aware retrieval.

Current fields:

- `id`
- `subject`
- `predicate`
- `object_id`
- `source_memory_id`
- `confidence`
- `valid_from`
- `valid_until`
- `metadata`
- `created_at`
- `updated_at`

Rules:

- Relationships are derived from source-grounded clean memory.
- `source_memory_id` points back to the memory that supports the edge.
- Open-ended validity is allowed, but `valid_until` must be after `valid_from` when both are present.
- Graphiti-style graph storage remains optional behind the memory graph port.

### ReviewDecision

Purpose: immutable human feedback event for future eval datasets.

Current fields:

- `id`
- `run_id`
- `operation_id`
- `decision`
- `reason`
- `metadata`
- `created_at`

Rules:

- Review actions should append a decision record instead of only mutating operation state.
- Rejection reasons are optional but should be preserved when provided.
- Eval export rows should include `run_id`, `operation_id`, `decision`, `reason`, operation kind, source memory IDs, source event IDs, proposed memory, rationale, confidence, and timestamps.

## Database Tables

Implemented or scaffolded tables:

- `raw_memory_events`
- `memory_units`
- `memory_sources`
- `memory_embeddings`
- `memory_relationships`
- `refactor_runs`
- `memory_operations`
- `review_decisions`
- `contradictions`
- `memory_versions`

Planned tables or columns:

- audit logs
- eval exports
- object archive references

## Canonical Versus Derived Data

Canonical:

- raw memory events
- memory units
- memory sources
- refactor runs
- memory operations
- review decisions
- contradictions
- memory versions

Derived:

- embeddings
- vector indexes
- graph projections
- prompt traces
- cost metrics
- dashboard aggregates
- archived raw object snapshots

Derived data can be rebuilt from canonical data. Canonical data needs transactions, migrations, and reviewable contracts.

## Invariants

- Raw memory events are append-only evidence.
- Clean memory is the default retrieval surface.
- Refactor agents output typed operations only.
- Unsupported claims should not become active memory.
- Approved apply must be transactional.
- Apply should write immutable versions.
- Archive and supersede are preferred over silent deletion.
- Contradictions should remain visible until resolved.
- Future systems must enter through adapters before becoming runtime requirements.
