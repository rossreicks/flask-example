.PHONY: dev test test-unit test-integration test-e2e lint format typecheck migrate migrate-new

dev:
	uv run flask --app app:create_app run --debug

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

test-e2e:
	uv run pytest tests/e2e

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check

migrate:
	uv run flask --app app:create_app db upgrade

migrate-new:
	uv run flask --app app:create_app db migrate -m "$(msg)"
