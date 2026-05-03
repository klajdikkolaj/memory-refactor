.PHONY: check-structure infra-up infra-down dev-web dev-api dev-worker test test-python test-python-unit test-python-integration migrate check-web test-web-unit test-web-e2e compose-config

check-structure:
	test -f AGENTS.md
	test -f docs/codex-context.md
	test -f apps/web/package.json
	test -f services/memory-engine/pyproject.toml
	test -f compose.yaml
	python -m compileall services/memory-engine/src

compose-config:
	docker compose config

infra-up:
	docker compose up -d postgres temporal temporal-ui

infra-down:
	docker compose down

dev-web:
	pnpm --filter @memory-refactor/web dev

dev-api:
	cd services/memory-engine && uv run uvicorn memory_refactor.api.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	cd services/memory-engine && uv run memory-worker

test-python:
	cd services/memory-engine && uv run --extra dev pytest

test-python-unit:
	cd services/memory-engine && uv run --extra dev pytest -m "not integration"

test-python-integration:
	cd services/memory-engine && RUN_INTEGRATION_TESTS=1 uv run --extra dev pytest -m integration

migrate:
	cd services/memory-engine && uv run --extra dev alembic upgrade head

check-web:
	pnpm --filter @memory-refactor/web lint
	pnpm --filter @memory-refactor/web typecheck

test-web-unit:
	pnpm --filter @memory-refactor/web test:unit

test-web-e2e:
	pnpm --filter @memory-refactor/web test:e2e

test: test-python-unit test-web-unit
