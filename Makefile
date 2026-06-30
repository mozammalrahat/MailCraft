.PHONY: help install dev run test test-cov lint fmt type-check migrate worker clean

# Default target
help:
	@echo "MailCraft — available commands:"
	@echo ""
	@echo "  make install      Install all dependencies (including dev)"
	@echo "  make dev          Run development server with auto-reload"
	@echo "  make run          Run production server"
	@echo "  make test         Run tests (no coverage)"
	@echo "  make test-cov     Run tests with coverage report"
	@echo "  make lint         Run Ruff linter"
	@echo "  make fmt          Run Ruff formatter (auto-fix)"
	@echo "  make type-check   Run pyrefly type checker"
	@echo "  make migrate      Apply pending Alembic migrations"
	@echo "  make worker       Start the ARQ background worker"
	@echo "  make eval         Run the evaluation suite"
	@echo "  make clean        Remove build artefacts and cache"

install:
	uv sync --all-groups

dev:
	DEBUG=true uv run mailcraft

run:
	uv run mailcraft

test:
	uv run pytest -x -q --no-cov

test-cov:
	uv run pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov

lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

type-check:
	uv run pyrefly check

migrate:
	uv run alembic upgrade head

worker:
	uv run mailcraft-worker

eval:
	uv run mailcraft-eval

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml dist build
