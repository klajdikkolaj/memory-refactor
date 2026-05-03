# Stories

Stories are user or operator outcomes. Each story links to an epic and should stay independent enough to become a small implementation slice.

Status legend:

- `todo`
- `in-progress`
- `done`
- `blocked`
- `deferred`

## E0: Repo Foundation And Operating Model

### S0.1: Bootstrap Product Monorepo

Status: `done`

As a developer, I want a clear monorepo structure so web, API, worker, infra, and docs work can evolve independently.

Acceptance criteria:

- `apps/web` exists for the Next.js UI.
- `services/memory-engine` exists for FastAPI and Temporal worker code.
- `infra` and `compose.yaml` exist for local infrastructure.
- `make check-structure` passes.

### S0.2: Establish Codex Operating Context

Status: `done`

As a developer using Codex, I want repo-local guidance so future sessions follow the same workflow and validation rules.

Acceptance criteria:

- `AGENTS.md` is short and operational.
- `docs/codex-context.md` explains the product and architecture boundaries.
- Repo-local skills exist for workflow, next task, handoff, and parallel work.
- Repo-specific skills exist for repeated DB, API, UI, memory-operation, test-gate, and ship workflows.
- Read-only reviewer agents exist for repeated database, UI, test-gate, and architecture review passes.

### S0.3: Track Product Work In Docs

Status: `done`

As a developer, I want epics, stories, and tasks in the repo so planning survives across sessions.

Acceptance criteria:

- `docs/epics.md`, `docs/stories.md`, and `docs/tasks.md` exist.
- Tasks reference story and epic IDs.
- Handoff and next-task guidance point to the tracking docs.

## E1: Memory Contracts And Persistence

### S1.1: Define Core Memory Contracts

Status: `done`

As an API developer, I want typed memory contracts so LLM output, API payloads, and database records share the same domain language.

Acceptance criteria:

- Pydantic models cover memory units, operations, plans, versions, sources, and contradictions.
- Contracts reject unknown fields where correctness matters.
- Tests cover representative operation creation.

### S1.2: Persist Memory Units

Status: `done`

As the system, I want to store memory units in Postgres so canonical memory has a transactional source of truth.

Acceptance criteria:

- SQLAlchemy model exists for `memory_units`.
- Alembic migration creates the table.
- API can create and list memory units.
- Tests cover persistence behavior.

### S1.3: Persist Refactor Runs And Operations

Status: `done`

As a reviewer, I want refactor runs and operations stored so Memory PRs can be inspected and applied later.

Acceptance criteria:

- Refactor run and operation tables exist.
- Preview endpoint persists a run instead of returning only seed data.
- Operations keep rationale, confidence, source memory IDs, and source event IDs.

## E2: Ingestion And Source Archive

### S2.1: Ingest Raw Memory Events

Status: `done`

As an integrator, I want to submit raw memory events so conversations and imports can enter the refactor pipeline.

Acceptance criteria:

- API endpoint accepts raw event payloads.
- Source content and metadata are stored.
- Validation errors are explicit.
- Manual pasted-memory batch flow can create multiple raw events and start a refactor run.

### S2.2: Preserve Raw Archives Behind A Port

Status: `deferred`

As an operator, I want raw archives stored outside Postgres when they are large so database records stay lean.

Acceptance criteria:

- Object storage interface exists.
- Local stub implementation works.
- R2/S3 implementation can be added without changing ingestion contracts.

## E3: Retrieval Layer

### S3.1: Add pgvector Embeddings

Status: `done`

As the refactor agent, I want semantic retrieval so related memories can be considered together.

Acceptance criteria:

- pgvector extension is enabled.
- Embedding table or column exists.
- Retrieval port can return nearest memory candidates.

### S3.2: Add Relationship Retrieval

Status: `done`

As the refactor agent, I want relationship-aware retrieval so old and current facts can be compared.

Acceptance criteria:

- Relationship table exists in Postgres for MVP.
- Temporal validity fields are represented.
- Graphiti-style integration remains optional.

## E4: Refactor Agent And Typed Operations

### S4.1: Implement Deterministic Refactor Planner Stub

Status: `done`

As a developer, I want a deterministic planner stub so API and workflow paths can be built before model integration.

Acceptance criteria:

- Stub returns a valid `RefactorPlan`.
- Stub is usable from API and Temporal activity code.
- Unit test covers the merge operation.

### S4.2: Wire Pydantic AI Refactor Agent

Status: `todo`

As a user, I want the system to propose high-quality memory operations from related memories.

Acceptance criteria:

- Agent returns schema-valid `RefactorPlan`.
- Invalid output is rejected or repaired safely.
- Prompt includes source evidence and operation constraints.

## E5: Durable Workflows

### S5.1: Run Refactor Workflow Through Temporal

Status: `done`

As an operator, I want memory refactor jobs to survive retries and restarts.

Acceptance criteria:

- API starts `RefactorMemoryWorkflow`.
- Worker executes planner activity.
- Workflow result references persisted run records.

### S5.2: Apply Approved Operations Transactionally

Status: `done`

As a reviewer, I want approved memory operations applied atomically so memory is never partially refactored.

Acceptance criteria:

- Apply endpoint validates operation status.
- Database transaction writes memory updates and versions.
- Failed apply leaves canonical memory unchanged.

## E6: Memory PR Review UI

### S6.1: Display Refactor Runs From API

Status: `done`

As a reviewer, I want the dashboard to show real refactor runs so I can choose what to inspect.

Acceptance criteria:

- Web app fetches runs from FastAPI.
- Loading and empty states exist.
- API errors are visible without breaking the whole screen.

### S6.2: Review Operation Detail And Sources

Status: `done`

As a reviewer, I want to inspect operation rationale and sources before approving memory changes.

Acceptance criteria:

- Operation detail panel uses API data.
- Source IDs and excerpts are visible.
- Contradictions have a distinct review state.

### S6.3: Approve Or Reject Operations

Status: `done`

As a reviewer, I want to approve or reject operations so only trusted memory changes are applied.

Acceptance criteria:

- Approve and reject actions call the API.
- UI state updates after action.
- Apply remains disabled when conflicts are unresolved.

## E7: Observability, Evals, And Cost Control

### S7.1: Add Trace IDs To Refactor Runs

Status: `todo`

As an operator, I want each run linked to trace metadata so model and workflow behavior can be debugged.

Acceptance criteria:

- Refactor run stores trace identifiers.
- API returns trace metadata.
- Instrumentation can be disabled locally.

### S7.2: Capture Human Feedback As Eval Data

Status: `todo`

As a product builder, I want rejects and edits to become evaluation data so the agent improves over time.

Acceptance criteria:

- Review decisions are stored.
- Rejection reasons can be captured.
- Export format for eval datasets is documented.

## E8: Future Infrastructure Scale-Out

### S8.1: Promote Qdrant Behind Vector Port

Status: `deferred`

As the system scales, I want Qdrant available without rewriting retrieval callers.

Acceptance criteria:

- Vector port has pgvector and Qdrant implementations.
- Cutover plan is documented.
- Benchmarks justify adoption.

### S8.2: Promote Event Stream Behind Event Port

Status: `deferred`

As the system grows, I want durable events for cross-service workflows without coupling the MVP to NATS.

Acceptance criteria:

- Event publisher port exists.
- NATS JetStream implementation is optional.
- Event names and payload contracts are documented.

## E9: Testing And Quality Gates

### S9.1: Document Test Strategy

Status: `done`

As a developer, I want a clear test strategy so backend, frontend, integration, and E2E expectations are explicit.

Acceptance criteria:

- `docs/testing-strategy.md` exists.
- Commands and test layers are documented.
- Runtime-dependent tests are clearly separated from unit tests.

### S9.2: Prepare Backend Test Harness

Status: `done`

As a backend developer, I want unit and integration test commands so persistence and API behavior can be verified safely.

Acceptance criteria:

- Pytest markers distinguish integration tests.
- Unit tests run without external services.
- Integration tests are skipped unless explicitly enabled.
- Repository behavior has at least one integration test scaffold.

### S9.3: Prepare Frontend Test Harness

Status: `done`

As a frontend developer, I want component and E2E test commands so the review UI can be verified before shipping.

Acceptance criteria:

- Vitest and React Testing Library are configured.
- Playwright is configured.
- The current dashboard has at least one component test and one E2E smoke test.

### S9.4: Add CI Quality Gate

Status: `todo`

As a maintainer, I want CI to run the default gate so regressions are caught before merge.

Acceptance criteria:

- CI installs Python and Node dependencies.
- CI runs structure, backend unit, frontend lint/type-check, and frontend unit tests.
- Integration tests are added as a separate job when Postgres is available.
