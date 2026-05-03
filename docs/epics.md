# Epics

Status legend:

- `planned`: not started
- `in-progress`: active work
- `done`: complete enough for the current phase
- `deferred`: intentionally later

## E0: Repo Foundation And Operating Model

Status: `in-progress`

Establish the monorepo, Codex workflow scaffold, local commands, docs, and validation rules needed to build safely.

Success criteria:

- Repo-local Codex instructions and skills exist.
- Web, API, worker, infra, and docs boundaries are clear.
- Basic structure checks pass.
- Future sessions can resume from docs without rebuilding context.

## E1: Memory Contracts And Persistence

Status: `in-progress`

Define durable memory primitives and persist them in Postgres as the source of truth.

Success criteria:

- `MemoryUnit`, `RawMemoryEvent`, `MemoryOperation`, `RefactorPlan`, `MemoryVersion`, and `Contradiction` have typed contracts.
- SQLAlchemy models and Alembic migrations exist.
- API endpoints can create, list, and inspect memory records.
- Approved operations write immutable version history.

## E2: Ingestion And Source Archive

Status: `planned`

Accept raw memory inputs from notes, conversations, imports, and API calls while preserving source evidence.

Success criteria:

- Raw memory event endpoint exists.
- Source excerpts and metadata are stored.
- Large archive storage is abstracted behind a port.
- R2/S3 can be added later without changing core contracts.

## E3: Retrieval Layer

Status: `planned`

Retrieve related memories by source, text, semantic similarity, and eventually temporal graph relationships.

Success criteria:

- pgvector embedding storage is available.
- Retrieval API returns source-grounded candidates.
- Qdrant is hidden behind a vector-index interface for later scale.
- Graph relationship retrieval can start in Postgres before Graphiti or Neo4j-style storage is added.

## E4: Refactor Agent And Typed Operations

Status: `planned`

Build the AI memory compiler that proposes schema-valid operations rather than free-form summaries.

Success criteria:

- Refactor agent produces validated `RefactorPlan` outputs.
- Invalid LLM output fails safely.
- Operations include rationale, confidence, source memory IDs, and review requirements.
- Model routing can move behind LiteLLM later.

## E5: Durable Workflows

Status: `planned`

Use Temporal for long-running memory refactor jobs, retries, review checkpoints, and transactional application.

Success criteria:

- Refactor workflow starts from API.
- Activities perform I/O outside deterministic workflow code.
- Failed runs are resumable and inspectable.
- Apply step is transactional and auditable.

## E6: Memory PR Review UI

Status: `in-progress`

Give users a product surface for reviewing memory operations, resolving contradictions, and applying approved changes.

Success criteria:

- Dashboard lists refactor runs and operations from the API.
- Users can approve, reject, or inspect operation sources.
- Contradictions are visually distinct.
- UI is verified in browser before shipping meaningful changes.

## E7: Observability, Evals, And Cost Control

Status: `planned`

Trace model calls, retrieval context, workflow execution, user decisions, cost, and quality signals.

Success criteria:

- Langfuse and OpenTelemetry are available behind optional instrumentation.
- Refactor runs have trace IDs.
- Rejected operations become evaluation data.
- Model cost and latency are visible per run.

## E8: Future Infrastructure Scale-Out

Status: `deferred`

Add Qdrant, Graphiti or graph storage, NATS JetStream, object storage, and Kubernetes only after the core loop proves the need.

Success criteria:

- Each future system has an adapter boundary.
- Optional services do not block local MVP development.
- Migration path is documented before adoption.

## E9: Testing And Quality Gates

Status: `in-progress`

Create a test environment that covers backend units, backend integration, Temporal workflows, frontend components, browser E2E, and future CI gates.

Success criteria:

- Testing strategy is documented.
- Backend unit and integration test commands exist.
- Frontend unit and E2E test commands exist.
- Runtime-dependent tests are gated so local unit tests stay fast.
- CI can run the default quality gate without manual setup.
