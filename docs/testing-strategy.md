# Testing Strategy

The goal is to keep the product safe while the architecture grows from MVP to infrastructure product. Tests should prove the memory compiler loop works before optional scale systems are introduced.

## Test Layers

| Layer | Scope | Command | Default Gate |
| --- | --- | --- | --- |
| Structure | Required files, Python syntax, Compose shape | `make check-structure` and `make compose-config` | every structural change |
| Backend unit | Pydantic contracts, pure domain logic, repository mapping | `make test-python-unit` | every backend change |
| Backend integration | Postgres, migrations, repository behavior, API persistence | `make test-python-integration` | persistence/API changes |
| Temporal workflow | Workflow determinism and activity boundaries | `make test-python-unit` initially; dedicated workflow tests later | workflow changes |
| Frontend lint/type-check | TypeScript and Next.js code quality | `make check-web` | every web change |
| Frontend unit/component | React components, state transitions, rendering | `make test-web-unit` | every web behavior change |
| Frontend E2E | Browser happy paths and key workflows | `make test-web-e2e` | review/apply UI changes |
| Cross-service smoke | Web + API + Postgres + Temporal | manual until CI exists | release or PR readiness |

## Backend Test Policy

Use pytest.

- Unit tests must not require Postgres, Temporal, network, or model providers.
- Integration tests must be marked with `@pytest.mark.integration`.
- Integration tests are skipped unless `RUN_INTEGRATION_TESTS=1` is set.
- Repository tests should exercise real SQL behavior against Postgres when marked integration.
- API tests should prefer FastAPI dependency overrides for unit-level behavior and real database sessions for integration-level behavior.
- Temporal workflows must keep I/O inside activities so workflow tests can stay deterministic.

## Frontend Test Policy

Use Vitest and React Testing Library for component tests. Use Playwright for browser E2E.

- Component tests cover rendering, selected states, filters, forms, and local transitions.
- E2E tests cover user-level flows: page loads, review queue scanning, operation detail, approve/reject, and error states.
- UI changes require browser verification when dependencies and runtime are available.
- Keep data-heavy UI test fixtures small and explicit.

## Integration And E2E Setup

Backend integration prerequisites:

```sh
make infra-up
cd services/memory-engine && uv run --extra dev alembic upgrade head
RUN_INTEGRATION_TESTS=1 uv run --extra dev pytest -m integration
```

Frontend E2E prerequisites:

```sh
pnpm install
pnpm --filter @memory-refactor/web exec playwright install
make test-web-e2e
```

## CI Plan

Initial PR gate:

1. `make check-structure`
2. `make test-python-unit`
3. `make check-web`
4. `make test-web-unit`

Persistence PR gate:

1. Start Postgres service.
2. Run Alembic migrations.
3. Run `make test-python-integration`.

UI PR gate:

1. Run web lint/type-check/unit tests.
2. Run Playwright E2E for changed flows.
3. Capture screenshot evidence when the visible product changes.

## Test Data Principles

- Prefer factories/builders over large opaque fixtures.
- Keep source evidence visible in fixtures.
- Use deterministic IDs where a test needs stable assertions.
- Do not hide LLM behavior behind brittle snapshot tests.
- Store rejected/edited memory operations as future evaluation data, not as ordinary unit-test fixtures.

## What Not To Test Yet

- Qdrant, NATS, Graphiti, LiteLLM, Langfuse, R2, and Kubernetes are optional future adapters. Do not add mandatory tests for them before the core memory PR loop is real.
- Browser E2E should stay focused on happy paths and critical failure states, not pixel-perfect assertions.
