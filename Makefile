.PHONY: check
check: lint test

.PHONY: lint
lint:
	uv run ruff format
	uv run ruff check --fix --show-fixes
	uv run mypy src/

.PHONY: test
test:
	uv run pytest

.PHONY: api
api:
	uv run uvicorn cloudflare_dyndns.api:app --reload
