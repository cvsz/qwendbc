# QwenDBC

[![CI](https://github.com/cvsz/qwendbc/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/cvsz/qwendbc/actions/workflows/ci-cd.yml)
[![CodeQL Analysis](https://github.com/cvsz/qwendbc/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/cvsz/qwendbc/actions/workflows/codeql.yml)
[![Dependency Review](https://github.com/cvsz/qwendbc/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/cvsz/qwendbc/actions/workflows/dependency-review.yml)
[![Release](https://github.com/cvsz/qwendbc/actions/workflows/release.yml/badge.svg)](https://github.com/cvsz/qwendbc/actions/workflows/release.yml)

QwenDBC is a local-first FastAPI + React application for running a GGUF Qwen model with `llama.cpp`, plus local document ingestion and semantic search with ChromaDB. When explicitly enabled, it can route free text chat through Kilo, OpenCode, and OpenRouter before falling back to a loaded local model.

## Current stack

- Backend: Python 3.13, FastAPI 0.141.x, Pydantic v2, llama-cpp-python 0.3.35+
- Retrieval: ChromaDB 1.5.x, sentence-transformers 6.x
- Frontend: React 19.2, Vite 8.2
- Runtime: Docker Compose, Nginx frontend reverse proxy
- Quality: Black, Flake8, mypy, pytest/coverage, oxlint, ShellCheck when shell scripts exist
- Security: CodeQL, dependency review, pip-audit, npm audit, Dependabot

> **Security boundary:** remote providers are disabled by default. When `QWENDBC_ACCESS_TOKEN` is configured, chat, model lifecycle, catalog refresh, and document routes require `Authorization: Bearer ...`; health remains readable. Docker and local development bind to loopback by default, and public deployment still needs an authenticated edge/app boundary.

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

Both published ports bind to `127.0.0.1` by default. `BIND_HOST=0.0.0.0` intentionally exposes the frontend and its `/api/` proxy to the network, so use it only when an authenticated edge and a non-empty `QWENDBC_ACCESS_TOKEN` are in place.

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

The FastAPI and Vite development servers listen on loopback by default. Vite proxies `/api/*` to the FastAPI backend on port 8000. The frontend's **Operator access** field stores only the application bearer token in the current browser session; provider keys are never entered into or bundled in the frontend.

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

### Model catalog and chat completion

Inspect the normalized provider catalog. It contains only eligible free text
models; remote providers appear only when `REMOTE_MODELS_ENABLED=true` and the
provider is configured.

```bash
curl http://localhost:8000/api/v1/models
```

Refresh remote catalogs only from an authorized operator session:

```bash
curl -X POST http://localhost:8000/api/v1/models/refresh \
  -H "Authorization: Bearer ${QWENDBC_ACCESS_TOKEN}"
```

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

Existing clients that send only `messages` continue to use the configured
default route. With remote mode enabled, include the application token. You
may optionally request a provider/model or ask the backend to retrieve local
document context:

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer ${QWENDBC_ACCESS_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Summarize the deployment notes"}],"provider":"openrouter","model":"openrouter/free","use_rag":true}'
```

Automatic free routing follows `FREE_PROVIDER_ORDER`—by default
`kilo,opencode,openrouter,local`. A provider is skipped on outage, rate limit,
timeout, missing eligible model, or configuration failure. The response's
`qwendbc` metadata identifies the selected provider/model and whether fallback
was used. Streaming preserves the existing SSE contract and only falls back
before the first content chunk.

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
- `MODEL_MODE`, `FREE_PROVIDER_ORDER`, and `REMOTE_MODELS_ENABLED`
- `QWENDBC_ACCESS_TOKEN`, `REMOTE_REQUEST_TIMEOUT_SECONDS`,
  `REMOTE_MAX_CONCURRENT_REQUESTS`, and `REMOTE_RATE_LIMIT_PER_MINUTE`
- `KILO_BASE_URL`, `KILO_API_KEY`, `KILO_MODEL`
- `OPENCODE_BASE_URL`, `OPENCODE_API_KEY`, `OPENCODE_FREE_MODEL`
- `OPENROUTER_BASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`

`REMOTE_MODELS_ENABLED` defaults to `false`. Enabling it requires a nonblank
`QWENDBC_ACCESS_TOKEN`; provider keys remain server-side and are optional only
where the provider supports authorized anonymous free access. The application
reads the project `.env` and process environment, not any shared
`/home/cvsz/.env.ai` file. Do not copy secrets from that operator reference
into Git or the browser.

The UI supports persisted `day`, `night`, and `system` themes. `system` follows
the browser's current color preference, and reduced-motion users receive no
nonessential transitions. The layout is mobile-first and keeps the provider,
model, RAG, and runtime controls keyboard accessible.

To roll back remote routing without a data migration, set either of these in
the deployment environment and restart the stack:

```dotenv
MODEL_MODE=local
# or
REMOTE_MODELS_ENABLED=false
```

`.env`, model files, vector-store data, virtual environments, caches, and frontend build outputs are ignored by Git.

## CI behavior

CI is intentionally blocking. Python lint/type/test/security failures, frontend lint/build/audit failures, Compose validation, and Docker build failures fail the workflow instead of being hidden behind `|| true` or `|| echo`.

The repository currently contains no tracked `.sh` scripts, so ShellCheck correctly reports that there is nothing to scan. The CI job becomes active automatically if shell scripts are added later.

The frontend commits `frontend/package-lock.json`; CI uses `npm ci`, runs the
Node helper tests, lint, production build, and high-severity npm audit.

## License

MIT
