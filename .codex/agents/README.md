# Repo Agents

These agents are read-only specialist reviewers. They should be used for repeated advisor and verification passes, not as the default implementation path.

## Available Agents

- `db_reviewer`: database schema, Alembic migrations, SQLAlchemy models, repository boundaries, transaction safety.
- `ui_verifier`: dashboard behavior, accessibility selectors, component tests, Playwright flows.
- `test_gate_reviewer`: maps a diff to required checks and generated-artifact risk.
- `architecture_synthesizer`: product boundaries, memory-operation invariants, ports/adapters, Temporal rules, deferred infrastructure.

## Usage Rules

- Keep agents read-only unless a future repeated implementation slice has a clear disjoint write scope.
- Agents should cite repo-local skills and docs instead of re-encoding policy.
- The main thread remains responsible for integration, final judgment, and user communication.
- Prefer a small number of focused agents over broad or overlapping reviews.
