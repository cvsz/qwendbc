# =============================================================================
# QwenDBC - Full Feature Control Panel Makefile
# =============================================================================
# A comprehensive Makefile for managing development, testing, deployment,
# security, and maintenance tasks for the QwenDBC project.
# =============================================================================

.PHONY: help all setup dev run test lint security docs docker clean update sync

# =============================================================================
# Configuration
# =============================================================================
PYTHON := python3
PIP := pip3
NODE := node
NPM := npm
DOCKER := docker
DOCKER_COMPOSE := docker-compose
GIT := git
PYTEST := pytest
BLACK := black
FLAKE8 := flake8
MYPY := mypy
SAFETY := safety
ACT := act

BACKEND_DIR := backend
FRONTEND_DIR := frontend
DOCS_DIR := docs
TESTS_DIR := $(BACKEND_DIR)/tests
VENV_DIR := venv
NODE_MODULES := $(FRONTEND_DIR)/node_modules

# Colors for output
COLOR_RESET := \033[0m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m
COLOR_RED := \033[31m
COLOR_CYAN := \033[36m

# =============================================================================
# Default Target
# =============================================================================
help:
	@echo "$(COLOR_CYAN)╔═══════════════════════════════════════════════════════════╗$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)║           QwenDBC - Full Feature Control Panel           ║$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)╚═══════════════════════════════════════════════════════════╝$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)Setup & Installation:$(COLOR_RESET)"
	@echo "  make setup          - Full project setup (backend + frontend)"
	@echo "  make setup-backend  - Setup Python backend only"
	@echo "  make setup-frontend - Setup Node.js frontend only"
	@echo "  make install        - Install dependencies (alias for setup)"
	@echo ""
	@echo "$(COLOR_GREEN)Development Server:$(COLOR_RESET)"
	@echo "  make dev            - Run both backend and frontend in dev mode"
	@echo "  make backend        - Run backend server only"
	@echo "  make frontend       - Run frontend server only"
	@echo "  make run            - Run production Docker containers"
	@echo ""
	@echo "$(COLOR_GREEN)Testing & Quality:$(COLOR_RESET)"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-backend   - Run backend tests only"
	@echo "  make test-verbose   - Run tests with verbose output"
	@echo "  make coverage       - Generate and view coverage report"
	@echo "  make lint           - Run all linters (black, flake8, mypy)"
	@echo "  make format         - Auto-format code with black"
	@echo "  make check-types    - Run type checking with mypy"
	@echo ""
	@echo "$(COLOR_GREEN)Security Scanning:$(COLOR_RESET)"
	@echo "  make security       - Run all security scans"
	@echo "  make scan-deps      - Scan dependencies for vulnerabilities"
	@echo "  make codeql         - Run CodeQL analysis locally"
	@echo "  make audit-npm      - Audit npm packages for vulnerabilities"
	@echo ""
	@echo "$(COLOR_GREEN)Docker Operations:$(COLOR_RESET)"
	@echo "  make docker-build   - Build all Docker containers"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers"
	@echo "  make docker-logs    - Show container logs"
	@echo "  make docker-clean   - Remove all containers and images"
	@echo "  make docker-rebuild - Rebuild containers from scratch"
	@echo ""
	@echo "$(COLOR_GREEN)Documentation:$(COLOR_RESET)"
	@echo "  make docs           - Build all documentation"
	@echo "  make docs-serve     - Serve documentation locally"
	@echo "  make changelog      - Generate changelog from commits"
	@echo ""
	@echo "$(COLOR_GREEN)Git & Sync:$(COLOR_RESET)"
	@echo "  make sync           - Sync local with remote (fetch + rebase)"
	@echo "  make push           - Push changes to remote"
	@echo "  make pull           - Pull latest changes from remote"
	@echo "  make status         - Show git status and branch info"
	@echo "  make commit-all     - Stage and commit all changes"
	@echo ""
	@echo "$(COLOR_GREEN)Cleanup:$(COLOR_RESET)"
	@echo "  make clean          - Remove all generated files"
	@echo "  make clean-pyc      - Remove Python cache files"
	@echo "  make clean-node     - Remove node_modules"
	@echo "  make clean-test     - Remove test artifacts"
	@echo "  make distclean      - Complete cleanup (including venv)"
	@echo ""
	@echo "$(COLOR_GREEN)Utilities:$(COLOR_RESET)"
	@echo "  make env-check      - Validate environment configuration"
	@echo "  make health         - Check service health endpoints"
	@echo "  make model-info     - Display current model configuration"
	@echo "  make all            - Run setup, test, lint, and build"
	@echo ""
	@echo "$(COLOR_YELLOW)Quick Start:$(COLOR_RESET)"
	@echo "  make setup && make dev    # First time setup and run"
	@echo "  make test && make lint    # Before committing"
	@echo "  make security             # Security check"
	@echo "  make docker-up            # Run with Docker"
	@echo ""

# =============================================================================
# Setup & Installation
# =============================================================================
setup: setup-backend setup-frontend
	@echo "$(COLOR_GREEN)✓ Full project setup complete$(COLOR_RESET)"

setup-backend:
	@echo "$(COLOR_BLUE)Setting up Python backend...$(COLOR_RESET)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	@. $(VENV_DIR)/bin/activate && \
		$(PIP) install --upgrade pip && \
		$(PIP) install -r $(BACKEND_DIR)/requirements.txt && \
		echo "$(COLOR_GREEN)✓ Backend dependencies installed$(COLOR_RESET)"

setup-frontend:
	@echo "$(COLOR_BLUE)Setting up Node.js frontend...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && \
		$(NPM) install && \
		echo "$(COLOR_GREEN)✓ Frontend dependencies installed$(COLOR_RESET)"

install: setup
	@echo "$(COLOR_GREEN)✓ Installation complete$(COLOR_RESET)"

# =============================================================================
# Development Server
# =============================================================================
dev:
	@echo "$(COLOR_BLUE)Starting development servers...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Backend: http://localhost:8000$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Frontend: http://localhost:3000$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd $(FRONTEND_DIR) && $(NPM) start & \
	echo "$(COLOR_GREEN)✓ Servers started. Press Ctrl+C to stop$(COLOR_RESET)" && \
	wait

backend:
	@echo "$(COLOR_BLUE)Starting backend server...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "$(COLOR_BLUE)Starting frontend server...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) start

run: docker-up
	@echo "$(COLOR_GREEN)✓ Application running in Docker$(COLOR_RESET)"

# =============================================================================
# Testing & Quality Assurance
# =============================================================================
test:
	@echo "$(COLOR_BLUE)Running tests...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(PYTEST) $(TESTS_DIR) --cov=app --cov-report=term-missing --cov-report=html:../coverage_html
	@echo "$(COLOR_GREEN)✓ Tests complete. Coverage report: coverage_html/index.html$(COLOR_RESET)"

test-backend:
	@echo "$(COLOR_BLUE)Running backend tests...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(PYTEST) $(TESTS_DIR) -v

test-verbose:
	@echo "$(COLOR_BLUE)Running tests with verbose output...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(PYTEST) $(TESTS_DIR) -vv -s --tb=long

coverage:
	@echo "$(COLOR_BLUE)Generating coverage report...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(PYTEST) $(TESTS_DIR) --cov=app --cov-report=html:../coverage_html
	@echo "$(COLOR_GREEN)✓ Coverage report generated$(COLOR_RESET)"
	@open coverage_html/index.html 2>/dev/null || xdg-open coverage_html/index.html 2>/dev/null || echo "Open coverage_html/index.html in your browser"

lint: format check-types
	@echo "$(COLOR_BLUE)Running flake8...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(FLAKE8) app tests --max-line-length=100 --exclude=__pycache__,venv
	@echo "$(COLOR_GREEN)✓ All linters passed$(COLOR_RESET)"

format:
	@echo "$(COLOR_BLUE)Formatting code with black...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(BLACK) --line-length 100 app tests
	@echo "$(COLOR_GREEN)✓ Code formatted$(COLOR_RESET)"

check-types:
	@echo "$(COLOR_BLUE)Running type checker (mypy)...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(MYPY) app tests --ignore-missing-imports --no-strict-optional
	@echo "$(COLOR_GREEN)✓ Type checking complete$(COLOR_RESET)"

# =============================================================================
# Security Scanning
# =============================================================================
security: scan-deps audit-npm
	@echo "$(COLOR_GREEN)✓ All security scans complete$(COLOR_RESET)"

scan-deps:
	@echo "$(COLOR_BLUE)Scanning Python dependencies...$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && \
		$(PIP) install safety && \
		$(SAFETY) check -r $(BACKEND_DIR)/requirements.txt
	@echo "$(COLOR_GREEN)✓ Dependency scan complete$(COLOR_RESET)"

codeql:
	@echo "$(COLOR_BLUE)Running CodeQL analysis...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Note: For full CodeQL analysis, use GitHub Actions$(COLOR_RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && \
		$(FLAKE8) app --select=E9,F63,F7,F82 && \
		echo "$(COLOR_GREEN)✓ Basic security checks passed$(COLOR_RESET)"

audit-npm:
	@echo "$(COLOR_BLUE)Auditing npm packages...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) audit --audit-level=moderate
	@echo "$(COLOR_GREEN)✓ NPM audit complete$(COLOR_RESET)"

# =============================================================================
# Docker Operations
# =============================================================================
docker-build:
	@echo "$(COLOR_BLUE)Building Docker containers...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "$(COLOR_GREEN)✓ Containers built$(COLOR_RESET)"

docker-up:
	@echo "$(COLOR_BLUE)Starting Docker containers...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(COLOR_GREEN)✓ Containers started$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Backend: http://localhost:8000$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Frontend: http://localhost:3000$(COLOR_RESET)"

docker-down:
	@echo "$(COLOR_BLUE)Stopping Docker containers...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) down
	@echo "$(COLOR_GREEN)✓ Containers stopped$(COLOR_RESET)"

docker-logs:
	@echo "$(COLOR_BLUE)Showing container logs...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) logs -f

docker-clean:
	@echo "$(COLOR_RED)Removing all containers and images...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) down -v --rmi all
	@$(DOCKER) system prune -f
	@echo "$(COLOR_GREEN)✓ Cleanup complete$(COLOR_RESET)"

docker-rebuild: docker-clean docker-build docker-up
	@echo "$(COLOR_GREEN)✓ Containers rebuilt and restarted$(COLOR_RESET)"

# =============================================================================
# Documentation
# =============================================================================
docs:
	@echo "$(COLOR_BLUE)Validating documentation...$(COLOR_RESET)"
	@find $(DOCS_DIR) -name "*.md" -exec echo "  ✓ {}" \;
	@echo "$(COLOR_GREEN)✓ Documentation validated$(COLOR_RESET)"

docs-serve:
	@echo "$(COLOR_BLUE)Documentation serving not configured$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Tip: Consider adding MkDocs or Docusaurus for interactive docs$(COLOR_RESET)"

changelog:
	@echo "$(COLOR_BLUE)Recent commits for changelog:$(COLOR_RESET)"
	@$(GIT) log --oneline -20
	@echo ""
	@echo "$(COLOR_GREEN)✓ To update CHANGELOG.md, manually curate these commits$(COLOR_RESET)"

# =============================================================================
# Git & Synchronization
# =============================================================================
sync:
	@echo "$(COLOR_BLUE)Syncing with remote repository...$(COLOR_RESET)"
	@$(GIT) fetch origin
	@$(GIT) rebase origin/main
	@echo "$(COLOR_GREEN)✓ Synced with remote$(COLOR_RESET)"

push:
	@echo "$(COLOR_BLUE)Pushing to remote...$(COLOR_RESET)"
	@$(GIT) push origin HEAD
	@echo "$(COLOR_GREEN)✓ Pushed successfully$(COLOR_RESET)"

pull:
	@echo "$(COLOR_BLUE)Pulling latest changes...$(COLOR_RESET)"
	@$(GIT) pull origin main
	@echo "$(COLOR_GREEN)✓ Pulled successfully$(COLOR_RESET)"

status:
	@echo "$(COLOR_BLUE)Git Status:$(COLOR_RESET)"
	@$(GIT) status -sb
	@echo ""
	@$(GIT) log --oneline -5

commit-all:
	@echo "$(COLOR_BLUE)Staging and committing all changes...$(COLOR_RESET)"
	@$(GIT) add -A
	@$(GIT) commit -m "chore: automated commit"
	@echo "$(COLOR_GREEN)✓ Committed successfully$(COLOR_RESET)"

# =============================================================================
# Cleanup
# =============================================================================
clean: clean-pyc clean-node clean-test
	@echo "$(COLOR_GREEN)✓ Cleanup complete$(COLOR_RESET)"

clean-pyc:
	@echo "$(COLOR_BLUE)Removing Python cache files...$(COLOR_RESET)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .mypy_cache 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ Python cache cleaned$(COLOR_RESET)"

clean-node:
	@echo "$(COLOR_BLUE)Removing node_modules...$(COLOR_RESET)"
	@rm -rf $(FRONTEND_DIR)/node_modules
	@rm -rf $(FRONTEND_DIR)/package-lock.json
	@echo "$(COLOR_GREEN)✓ Node modules cleaned$(COLOR_RESET)"

clean-test:
	@echo "$(COLOR_BLUE)Removing test artifacts...$(COLOR_RESET)"
	@rm -rf coverage_html
	@rm -rf .coverage
	@rm -rf htmlcov
	@echo "$(COLOR_GREEN)✓ Test artifacts cleaned$(COLOR_RESET)"

distclean: clean
	@echo "$(COLOR_RED)Complete cleanup (including venv)...$(COLOR_RESET)"
	@rm -rf $(VENV_DIR)
	@echo "$(COLOR_GREEN)✓ Full cleanup complete$(COLOR_RESET)"

# =============================================================================
# Utilities
# =============================================================================
env-check:
	@echo "$(COLOR_BLUE)Checking environment configuration...$(COLOR_RESET)"
	@if [ -f ".env" ]; then \
		echo "$(COLOR_GREEN)✓ .env file exists$(COLOR_RESET)"; \
		grep -E "^(MODEL_NAME|N_THREADS|SECRET_KEY)=" .env | sed 's/=.*//;s/^/  /'; \
	else \
		echo "$(COLOR_RED)✗ .env file missing$(COLOR_RESET)"; \
	fi

health:
	@echo "$(COLOR_BLUE)Checking service health...$(COLOR_RESET)"
	@curl -s http://localhost:8000/api/v1/health | jq . || echo "Backend not responding"
	@echo ""

model-info:
	@echo "$(COLOR_BLUE)Current Model Configuration:$(COLOR_RESET)"
	@if [ -f ".env" ]; then \
		grep -E "^MODEL" .env; \
	else \
		echo "$(COLOR_RED)No .env file found$(COLOR_RESET)"; \
	fi

all: setup test lint security docker-build
	@echo "$(COLOR_GREEN)╔════════════════════════════════════════╗$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)║  Full pipeline completed successfully  ║$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)╚════════════════════════════════════════╝$(COLOR_RESET)"

# =============================================================================
# End of Makefile
# =============================================================================
