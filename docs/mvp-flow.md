# MVP Flow

## Goal

The MVP proves the core memory refactor loop:

```txt
messy memory input -> raw events -> durable refactor run -> Memory PR -> approved clean memory -> retrieval
```

It should feel more like reviewing a code refactor than receiving an opaque AI summary.

## Current Manual Flow

The current backend supports both single raw event ingestion and a manual pasted-memory batch flow that creates raw events and starts a refactor run.

### 1. Ingest Raw Memory Events

Endpoint:

```http
POST /raw-memory-events
```

Example request:

```json
{
  "source_type": "manual",
  "source_id": "demo-batch-001",
  "content": "I use Go, React, NestJS, and Vue. I am learning ML/AI because I want to become a reinforcement learning developer.",
  "metadata": {
    "batch": "demo"
  }
}
```

The event is stored as append-only evidence. It is not canonical clean memory.

For pasted demos, use the batch endpoint:

```http
POST /raw-memory-events/manual-batches
```

Example request:

```json
{
  "source_id": "demo-batch-001",
  "content": "I use Go, React, NestJS, and Vue.\nI want to become an RL developer.",
  "metadata": {
    "demo": true
  }
}
```

The API creates one `manual` raw event per non-empty line, preserves the shared batch source ID, adds line metadata, and starts the refactor workflow with those raw event IDs.

### 2. Start A Refactor Run

Endpoint:

```http
POST /refactor-runs
```

Example request:

```json
{
  "raw_event_ids": ["evt_demo_001", "evt_demo_002"]
}
```

The API validates that the raw events exist, creates a run shell, then starts a Temporal workflow.

### 3. Workflow Produces A Plan

The Temporal workflow delegates I/O to activities. The activity loads raw events, builds a `RefactorPlan`, persists the plan, and marks events processed after a durable plan path exists.

Current implementation uses a deterministic planner stub so the API, database, UI, and workflow boundaries can be built before model integration.

### 4. Persist A Memory PR

A refactor run becomes a reviewable Memory PR:

```json
{
  "run_id": "run_demo_001",
  "status": "needs_review",
  "summary": "Created source-grounded memories from the pasted batch.",
  "input_event_ids": ["evt_demo_001", "evt_demo_002"],
  "operations": [
    {
      "operation": "create_memory",
      "source_event_ids": ["evt_demo_001"],
      "source_memory_ids": [],
      "rationale": "The raw event explicitly states the user's current programming stack.",
      "confidence": 0.94,
      "requires_human_review": true,
      "review_status": "needs_review",
      "proposed_memory": {
        "kind": "skill",
        "content": "The user mainly works with Go, React, NestJS, and Vue.",
        "confidence": 0.94,
        "status": "active",
        "sources": [
          {
            "source_type": "manual",
            "source_id": "demo-batch-001",
            "raw_event_id": "evt_demo_001"
          }
        ]
      }
    }
  ]
}
```

### 5. Review In The UI

The review UI should show:

- created memories
- updated memories
- merges
- archives
- supersessions
- contradictions
- rationale and confidence
- source event IDs and excerpts

The UI currently loads API-backed runs and operations, shows rationale and source excerpts, and can persist approve/reject decisions back to the memory operation review state.

Review endpoint:

```http
PATCH /refactor-runs/{run_id}/operations/{operation_id}/review
```

Example request:

```json
{
  "decision": "approved"
}
```

### 6. Apply Approved Operations

The MVP apply path supports approved `create_memory` operations. It is deterministic and transactional:

1. Validate the operation still references valid source evidence.
2. Validate the review status allows apply.
3. Write canonical memory changes.
4. Write immutable memory versions.
5. Mark operations applied.
6. Leave canonical memory unchanged if any step fails.

Apply endpoint:

```http
POST /refactor-runs/{run_id}/operations/{operation_id}/apply
```

Example response:

```json
{
  "operation": {
    "id": "op_demo_001",
    "review_status": "applied"
  },
  "memory": {
    "id": "mem_demo_001",
    "kind": "summary",
    "content": "The user mainly works with Go, React, NestJS, and Vue."
  }
}
```

Merge, split, supersede, archive, and contradiction apply semantics remain future slices.

### 7. Retrieve Clean Memory

Retrieval should return clean memory units, not raw events by default.

Future endpoint shape:

```http
POST /memory/retrieve
```

Example response:

```json
{
  "memories": [
    {
      "kind": "skill",
      "content": "The user mainly works with Go, React, NestJS, and Vue.",
      "confidence": 0.94
    },
    {
      "kind": "goal",
      "content": "The user is learning ML/AI with the goal of becoming a reinforcement learning developer.",
      "confidence": 0.91
    }
  ]
}
```

## Demo Scenario

Input:

```txt
I use Go, React, NestJS, and Vue.
I want to become a great software developer.
I am learning ML/AI because I want to become an RL developer.
Later I want to explore quantum software development.
I like detailed explanations with examples.
```

Expected clean memories:

```json
[
  {
    "kind": "skill",
    "content": "The user mainly works with Go, React, NestJS, and Vue.",
    "confidence": 0.95
  },
  {
    "kind": "goal",
    "content": "The user wants to become a strong software developer, specialize in reinforcement learning, and later explore quantum software development.",
    "confidence": 0.92
  },
  {
    "kind": "preference",
    "content": "The user prefers detailed explanations with practical examples.",
    "confidence": 0.93
  }
]
```

## Implementation Order

1. `S4.2`: wire the Pydantic AI refactor agent behind the planner port.
2. Expand apply semantics beyond `create_memory`.
3. Expand apply semantics beyond `create_memory`.
