# Contributing to QwenDBC

Thank you for contributing to QwenDBC. Keep changes focused, testable, and aligned with the repository's local-first security model.

## Prerequisites

- Python 3.13
- Node.js 24
- Docker with Docker Compose v2 (`docker compose`)
- GNU Make
- ShellCheck when adding or changing `.sh` files

## Setup

From the repository root:

```bash
make setup
```

This creates `.venv`, installs backend development dependencies, installs frontend dependencies, and creates a local `.env` from `configs/.env.example` when one does not already exist.

Run both development servers with:

```bash
make dev
```

The backend listens on `http://localhost:8000` and Vite on `http://localhost:3000`.

## Before opening a pull request

Run the same blocking checks used by CI:

```bash
make lint
make test
make security
make shellcheck   # required when shell scripts are present
make docker-build
```

After `npm install`, include the generated `frontend/package-lock.json` in dependency or frontend changes so CI and container builds can use reproducible installs.

## Backend standards

Backend code lives under `backend/app` and uses FastAPI, Pydantic v2, and Python type hints.

- Format with Black at 100 columns: `make format`.
- `make lint` is check-only; it must not rewrite source.
- Flake8 and mypy must pass without ignored exit codes.
- Use `model_dump()` and Pydantic v2 `ConfigDict` / `SettingsConfigDict` APIs.
- Keep blocking work out of the ASGI event loop. Use `asyncio.to_thread()` or a synchronous streaming iterator for CPU-bound/synchronous libraries.
- Do not log prompts, document contents, credentials, or other sensitive payloads by default.
- Add or update pytest coverage for behavior changes.

Run only backend tests with:

```bash
make test-backend
```

## Frontend standards

The frontend is React 19 on Vite 8 and uses oxlint.

```bash
cd frontend
npm run lint
npm run build
```

Keep API calls same-origin (`/api/v1`) unless a deployment explicitly requires `VITE_API_URL`. Always check `response.ok` before treating a request as successful, and display non-sensitive error messages to users.

The repository currently gates frontend changes with lint and production build checks. Add a dedicated frontend test framework before claiming frontend unit-test coverage.

## RAG changes

Document ingestion and semantic search live in `backend/app/services/rag_service.py` and `backend/app/routers/documents.py`.

Tests should normally override the RAG dependency with a fake service so API tests remain deterministic and do not download embedding models. Changes to ChromaDB or sentence-transformers integration should also be verified manually or in an integration environment with the real dependencies available.

## Configuration and secrets

- Never commit `.env`, API keys, tokens, model cache paths, or local GGUF files.
- Add new public configuration examples to `configs/.env.example`.
- Keep CORS origins explicit in deployments; do not use wildcard origins with credentials.
- If a real credential has ever been committed, remove it from current files **and rotate it**. Removing a file from the latest tree does not invalidate a leaked credential in Git history.

## Docker

Validate and build both services with:

```bash
make docker-build
```

Run the stack with:

```bash
make docker-up
```

The production frontend image is served by Nginx and proxies `/api/` to the backend container.

## Git and pull requests

1. Start from an updated `main` branch.
2. Create a focused branch such as `fix/streaming-block` or `feat/document-search`.
3. Use clear Conventional Commit-style messages when practical.
4. Keep generated artifacts and local model files out of commits.
5. Run all applicable checks above.
6. Explain behavior changes, security implications, and test evidence in the pull request.

Do not enable automatic merging until `main` is protected by repository rules requiring the relevant CI checks.

## Security reports

For suspected vulnerabilities, follow `SECURITY.md` rather than posting sensitive exploit details in a public issue.
