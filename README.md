# QwenDBC

[![CI](https://github.com/cvsz/qwendbc/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/cvsz/qwendbc/actions/workflows/ci-cd.yml)
[![CodeQL Analysis](https://github.com/cvsz/qwendbc/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/cvsz/qwendbc/actions/workflows/codeql.yml)
[![Dependency Review](https://github.com/cvsz/qwendbc/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/cvsz/qwendbc/actions/workflows/dependency-review.yml)
[![Release](https://github.com/cvsz/qwendbc/actions/workflows/release.yml/badge.svg)](https://github.com/cvsz/qwendbc/actions/workflows/release.yml)

QwenDBC is a local-first FastAPI + React application for running a GGUF Qwen model with `llama.cpp`, plus local document ingestion and semantic search with ChromaDB.

## Current stack

- Backend: Python 3.13, FastAPI 0.141.x, Pydantic v2, llama-cpp-python 0.3.35+
- Retrieval: ChromaDB 1.5.x, sentence-transformers 6.x
- Frontend: React 19.2, Vite 8.2
- Runtime: Docker Compose, Nginx frontend reverse proxy
- Quality: Black, Flake8, mypy, pytest/coverage, oxlint, ShellCheck when shell scripts exist
- Security: CodeQL, dependency review, pip-audit, npm audit, Dependabot

> **Security boundary:** this project does not implement authentication. Docker and local development bind to loopback by default. Keep that default unless the application is protected by an authenticated reverse proxy, VPN, zero-trust access layer, or equivalent control.

## Quick start with Docker

```bash
make install
```

`make install` creates `.env` from `configs/.env.example` when needed, validates
the Compose configuration, builds both images, starts the full stack, and waits
for the services to become healthy. Adjust `N_THREADS` and other settings in
`.env` before running it if needed. To stop the stack, use `make docker-down`.

The equivalent lower-level command is:

```bash
cp configs/.env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs

Both published ports bind to `127.0.0.1` by default. `BIND_HOST=0.0.0.0` intentionally exposes the frontend and its `/api/` proxy to the network, so use it only when access control is already in place.

If the default host ports are already in use, override them through Make:

```bash
make install BACKEND_HOST_PORT=8100 FRONTEND_HOST_PORT=3100
```

The Makefile health and status targets use the same port variables.

The first model load downloads the configured GGUF file into the Docker `model_data` volume. The repository does **not** track local GGUF files or Hugging Face cache symlinks.

Docker loads `configs/.env.example` into the backend container and then applies an optional root `.env` as an override. Container-only paths (`MODEL_PATH` and `CHROMA_DB_PATH`) are overridden by Compose so all other documented settings work consistently in Docker.

## Local development

Prerequisites: Python 3.13, Node.js 24, and standard build tools required by `llama-cpp-python`.

```bash
make setup
make dev
```

The FastAPI and Vite development servers listen on loopback by default. Vite proxies `/api/*` to the FastAPI backend on port 8000. To make a development server reachable from another host, opt in explicitly and protect the resulting unauthenticated API exposure.

## Quality gates

```bash
make lint
make test
make security
make shellcheck   # reports "No tracked .sh files" until shell scripts are added
make docker-build
```

`make lint` is check-only; it no longer modifies source files. Use `make format` when you explicitly want Black to rewrite Python files. ShellCheck scans tracked shell scripts only, so dependency/vendor scripts under `.venv` or `node_modules` are never linted as project source.

## API

### Health

```bash
curl http://localhost:8000/api/v1/health
```

### Model lifecycle

```bash
curl -X POST http://localhost:8000/api/v1/model/load
curl http://localhost:8000/api/v1/model/info
curl -X POST http://localhost:8000/api/v1/model/unload
```

### Chat completion

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

Streaming SSE is available at `/api/v1/chat/completions/stream`.

`max_tokens` cannot exceed the configured `MAX_CONTEXT_LENGTH`. If the client omits generation parameters, the backend uses `TEMPERATURE`, `TOP_P`, and `MAX_TOKENS` from configuration.

### Local document retrieval

Upload UTF-8 text:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F 'file=@notes.txt;type=text/plain'
```

Search indexed chunks:

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"deployment steps","top_k":5}'
```

Document indexing is lazy: ChromaDB and the embedding model initialize on the first upload/search request. This keeps normal chat startup lighter.

## Configuration

Copy `configs/.env.example` to the repository root as `.env`. Important settings include:

- `HOST`, `PORT`, and Docker host publishing via `BIND_HOST`
- `MODEL_NAME`, `MODEL_FILE`, `MODEL_PATH`
- `N_THREADS`, `N_BATCH`, `MAX_CONTEXT_LENGTH`
- `TEMPERATURE`, `TOP_P`, `MAX_TOKENS`
- `CHROMA_DB_PATH`, `EMBEDDING_MODEL`, `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`
- `MAX_UPLOAD_BYTES`
- `ALLOWED_ORIGINS`

`.env`, model files, vector-store data, virtual environments, caches, and frontend build outputs are ignored by Git.

## CI behavior

CI is intentionally blocking. Python lint/type/test/security failures, frontend lint/build/audit failures, Compose validation, and Docker build failures fail the workflow instead of being hidden behind `|| true` or `|| echo`.

The repository currently contains no tracked `.sh` scripts, so ShellCheck correctly reports that there is nothing to scan. The CI job becomes active automatically if shell scripts are added later.

The frontend still needs a committed `frontend/package-lock.json` for fully reproducible npm installs. Until that lockfile is generated and committed, CI and Docker emit/install from the exact top-level versions in `package.json`, but transitive npm resolution can still change.

## License

MIT
