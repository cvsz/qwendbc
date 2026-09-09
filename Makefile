SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON_SYSTEM ?= python3
NPM ?= npm
DOCKER ?= docker
DEV_HOST ?= 127.0.0.1
BACKEND_HOST_PORT ?= 8000
FRONTEND_HOST_PORT ?= 3000
COMPOSE_ENV := BACKEND_HOST_PORT=$(BACKEND_HOST_PORT) FRONTEND_HOST_PORT=$(FRONTEND_HOST_PORT)
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy
PIP_AUDIT := $(VENV)/bin/pip-audit
# llama-cpp-python requires diskcache at import time, but QwenDBC never enables
# LlamaDiskCache. The current diskcache advisory has no upstream fix; the
# container runs non-root with read-only storage, so keep this exception
# explicit and revisit it whenever the LLM dependency changes.
PIP_AUDIT_IGNORES := --ignore-vuln PYSEC-2026-2447
UVICORN := $(VENV)/bin/uvicorn

.PHONY: help install full-stack full-stack-install full-feature fullfeature setup setup-backend setup-frontend init-env dev backend frontend \
        test test-backend test-frontend lint lint-backend lint-frontend format \
        security shellcheck docker-build docker-up docker-down docker-logs \
        docker-clean health model-info clean all

help:
	@printf '%s\n' \
	  'QwenDBC targets:' \
	  '  make install           Build/start Docker full stack (alias: full-stack)' \
	  '  make full-stack        Build/start Docker full stack (override host ports if needed)' \
	  '  make setup             Install backend + frontend dependencies and create .env' \
	  '  make dev               Run backend and frontend development servers' \
	  '  make test              Run backend tests and frontend lint/build checks' \
	  '  make lint              Run Python and frontend linters without modifying files' \
	  '  make format            Format Python source with Black' \
	  '  make security          Audit Python and npm dependencies' \
	  '  make shellcheck        ShellCheck tracked .sh files when present' \
	  '  make docker-build      Validate Compose and build both images' \
	  '  make docker-up         Start the application with Docker Compose' \
	  '  make docker-down       Stop the Compose application' \
	  '  make docker-clean      Stop Compose and remove named volumes' \
	  '  make health            Query the backend health endpoint' \
	  '  make model-info        Query the backend model/info endpoint' \
	  '  make clean             Remove local build/test artifacts (keeps lockfiles)' \
	  '  make all               setup + lint + test + security + docker-build' \
	  '  make fullfeature       Full quality + feature gate: setup, lint, test, security,' \
	  '                         shellcheck, docker-build, docker-up, health, model-info, clean' \
	  '  make full-feature      Alias of fullfeature'

install: full-stack-install

full-stack-install: init-env
	$(COMPOSE_ENV) $(DOCKER) compose config --quiet
	$(COMPOSE_ENV) $(DOCKER) compose up -d --build --wait
	@printf '%s\n' \
	  'QwenDBC full stack is running:' \
	  '  Frontend: http://localhost:$(FRONTEND_HOST_PORT)' \
	  '  Backend:  http://localhost:$(BACKEND_HOST_PORT)' \
	  '  API docs: http://localhost:$(BACKEND_HOST_PORT)/docs' \
	  'Model files are downloaded only when the model-load endpoint is called.'

# full-stack: convenience alias for full-stack-install.
full-stack: full-stack-install

$(VENV)/bin/python:
	$(PYTHON_SYSTEM) -m venv $(VENV)

init-env:
	@if [[ ! -f .env ]]; then cp configs/.env.example .env; echo 'Created .env from configs/.env.example'; fi

setup-backend: $(VENV)/bin/python
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r backend/requirements-dev.txt

setup-frontend:
	@cd frontend && \
	  if [[ -f package-lock.json ]]; then \
	    $(NPM) ci --no-audit --no-fund; \
	  else \
	    $(NPM) install --no-audit --no-fund; \
	  fi

setup: init-env setup-backend setup-frontend

backend: $(VENV)/bin/python
	PYTHONPATH=backend $(UVICORN) app.main:app --reload --host $(DEV_HOST) --port 8000

frontend:
	cd frontend && $(NPM) run dev

dev: $(VENV)/bin/python
	@set -eu; \
	  PYTHONPATH=backend $(UVICORN) app.main:app --reload --host $(DEV_HOST) --port 8000 & backend_pid=$$!; \
	  (cd frontend && $(NPM) run dev) & frontend_pid=$$!; \
	  cleanup() { kill $$backend_pid $$frontend_pid 2>/dev/null || true; }; \
	  trap cleanup EXIT INT TERM; \
	  wait -n $$backend_pid $$frontend_pid

test-backend: $(VENV)/bin/python
	PYTHONPATH=backend $(PYTEST) -c backend/pyproject.toml backend/tests --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && $(NPM) test && $(NPM) run lint && $(NPM) run build

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
	$(PIP_AUDIT) -r backend/requirements.txt $(PIP_AUDIT_IGNORES)
	cd frontend && $(NPM) audit --audit-level=high

shellcheck:
	@command -v shellcheck >/dev/null 2>&1 || { echo 'shellcheck is not installed'; exit 2; }
	@mapfile -d '' scripts < <(git ls-files -z -- '*.sh'); \
	  if (( $${#scripts[@]} == 0 )); then \
	    echo 'No tracked .sh files to check.'; \
	  else \
	    shellcheck "$${scripts[@]}"; \
	  fi

docker-build:
	$(COMPOSE_ENV) $(DOCKER) compose config --quiet
	$(COMPOSE_ENV) $(DOCKER) compose build

docker-up:
	$(COMPOSE_ENV) $(DOCKER) compose up -d --build

docker-down:
	$(COMPOSE_ENV) $(DOCKER) compose down --remove-orphans

docker-logs:
	$(COMPOSE_ENV) $(DOCKER) compose logs -f

docker-clean:
	$(COMPOSE_ENV) $(DOCKER) compose down -v --remove-orphans

health:
	@curl -fsS http://localhost:$(BACKEND_HOST_PORT)/api/v1/health | $(PYTHON_SYSTEM) -m json.tool

model-info:
	@curl -fsS http://localhost:$(BACKEND_HOST_PORT)/api/v1/model/info | $(PYTHON_SYSTEM) -m json.tool

clean:
	rm -rf .pytest_cache .mypy_cache coverage_html htmlcov .coverage coverage.xml
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/htmlcov backend/.coverage
	rm -rf frontend/dist frontend/build
	find backend -type d -name __pycache__ -prune -exec rm -rf {} +

all: setup lint test security docker-build

# full-feature: alias of fullfeature (full quality + feature gate).
full-feature: fullfeature

# fullfeature: end-to-end quality + feature gate.
# Runs the full pipeline (setup, lint, test, security, shellcheck, docker-build,
# docker-up) and then verifies the running stack with health and model-info
# probes before cleaning up local artifacts. Fails on the first error.
fullfeature: setup lint test security shellcheck docker-build docker-up
	@echo '--- fullfeature: verifying running stack ---'
	@-$(MAKE) health
	@-$(MAKE) model-info
	@$(COMPOSE_ENV) $(MAKE) docker-down
	@$(MAKE) clean
	@echo 'fullfeature: all gates passed'
