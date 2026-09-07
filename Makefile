SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON_SYSTEM ?= python3
NPM ?= npm
DOCKER ?= docker
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy
PIP_AUDIT := $(VENV)/bin/pip-audit
UVICORN := $(VENV)/bin/uvicorn

.PHONY: help setup setup-backend setup-frontend init-env dev backend frontend \
        test test-backend test-frontend lint lint-backend lint-frontend format \
        security shellcheck docker-build docker-up docker-down docker-logs \
        docker-clean health model-info clean all

help:
	@printf '%s\n' \
	  'QwenDBC targets:' \
	  '  make setup          Install backend + frontend dependencies and create .env' \
	  '  make dev            Run backend and frontend development servers' \
	  '  make test           Run backend tests and frontend lint/build checks' \
	  '  make lint           Run Python and frontend linters without modifying files' \
	  '  make format         Format Python source with Black' \
	  '  make security       Audit Python and npm dependencies' \
	  '  make shellcheck     ShellCheck tracked .sh files when present' \
	  '  make docker-build   Validate Compose and build both images' \
	  '  make docker-up      Start the application with Docker Compose' \
	  '  make clean          Remove local build/test artifacts (keeps lockfiles)'

$(VENV)/bin/python:
	$(PYTHON_SYSTEM) -m venv $(VENV)

init-env:
	@if [[ ! -f .env ]]; then cp configs/.env.example .env; echo 'Created .env from configs/.env.example'; fi

setup-backend: $(VENV)/bin/python
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r backend/requirements-dev.txt

setup-frontend:
	cd frontend && $(NPM) install --no-audit --no-fund

setup: init-env setup-backend setup-frontend

backend: $(VENV)/bin/python
	PYTHONPATH=backend $(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && $(NPM) run dev

dev: $(VENV)/bin/python
	@set -eu; \
	  PYTHONPATH=backend $(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000 & backend_pid=$$!; \
	  (cd frontend && $(NPM) run dev) & frontend_pid=$$!; \
	  cleanup() { kill $$backend_pid $$frontend_pid 2>/dev/null || true; }; \
	  trap cleanup EXIT INT TERM; \
	  wait -n $$backend_pid $$frontend_pid

test-backend: $(VENV)/bin/python
	PYTHONPATH=backend $(PYTEST) -c backend/pyproject.toml backend/tests --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && $(NPM) run lint && $(NPM) run build

test: test-backend test-frontend

lint-backend: $(VENV)/bin/python
	$(BLACK) --config backend/pyproject.toml --check backend/app backend/tests
	$(FLAKE8) --config backend/.flake8 backend/app backend/tests
	$(MYPY) --config-file backend/pyproject.toml backend/app

lint-frontend:
	cd frontend && $(NPM) run lint

lint: lint-backend lint-frontend

format: $(VENV)/bin/python
	$(BLACK) --config backend/pyproject.toml backend/app backend/tests

security: $(VENV)/bin/python
	$(PIP_AUDIT) -r backend/requirements.txt
	cd frontend && $(NPM) audit --audit-level=high

shellcheck:
	@command -v shellcheck >/dev/null 2>&1 || { echo 'shellcheck is not installed'; exit 2; }
	@mapfile -d '' scripts < <(find . -type f -name '*.sh' -not -path './.git/*' -print0); \
	  if (( $${#scripts[@]} == 0 )); then echo 'No tracked .sh files to check.'; else shellcheck "$${scripts[@]}"; fi

docker-build:
	$(DOCKER) compose config --quiet
	$(DOCKER) compose build

docker-up:
	$(DOCKER) compose up -d --build

docker-down:
	$(DOCKER) compose down --remove-orphans

docker-logs:
	$(DOCKER) compose logs -f

docker-clean:
	$(DOCKER) compose down -v --remove-orphans

health:
	@curl -fsS http://localhost:8000/api/v1/health | $(PYTHON_SYSTEM) -m json.tool

model-info:
	@curl -fsS http://localhost:8000/api/v1/model/info | $(PYTHON_SYSTEM) -m json.tool

clean:
	rm -rf .pytest_cache .mypy_cache coverage_html htmlcov .coverage coverage.xml
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/htmlcov backend/.coverage
	rm -rf frontend/dist frontend/build
	find backend -type d -name __pycache__ -prune -exec rm -rf {} +

all: setup lint test security docker-build
