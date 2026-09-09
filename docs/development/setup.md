# Development Setup

This guide covers a reproducible local development loop for QwenDBC.

## Prerequisites

- Python 3.13;
- Node.js 24 and npm;
- GNU Make and Git;
- native build tools required by `llama-cpp-python`;
- Docker Engine with Compose v2.24+ for container validation.

The repository's CI uses Python 3.13 and Node 24. Keep local tool versions
aligned with those jobs when diagnosing differences.

## Setup

From the repository root:

```bash
make setup
```

This creates `.venv`, installs backend development dependencies, installs the
frontend dependencies with `npm ci` when the lockfile is present, and creates
the ignored root `.env` from `configs/.env.example` if needed.

For a manual backend setup:

```bash
uv venv .venv --python 3.13
. .venv/bin/activate
uv pip install -r backend/requirements-dev.txt
```

For a manual frontend setup:

```bash
cd frontend
npm ci
cd ..
```

Do not commit `.env`, model files, embedding caches, RAG data, `.venv`,
`node_modules`, or build output.

## Configuration

Use `configs/.env.example` as the source of non-secret settings. Development
defaults bind to loopback, keep remote providers disabled, and allow the local
API without a token. To exercise protected routes, set a local test token and
send it as a bearer header; never use a production credential in development.

Important settings include:

- `MODEL_NAME`, `MODEL_FILE`, `MODEL_PATH`, `N_THREADS`, `N_BATCH`, and
  `MAX_CONTEXT_LENGTH` for local inference;
- `MODEL_MODE`, `FREE_PROVIDER_ORDER`, `REMOTE_MODELS_ENABLED`, and the
  backend-only provider settings for optional free routing;
- `QWENDBC_ACCESS_TOKEN`, `REMOTE_RATE_LIMIT_PER_MINUTE`, and
  `REMOTE_MAX_CONCURRENT_REQUESTS` for access/remote limits;
- `CHROMA_DB_PATH`, `EMBEDDING_MODEL`, `RAG_CHUNK_SIZE`,
  `RAG_CHUNK_OVERLAP`, `RAG_EMBED_BATCH_SIZE`, `MAX_RAG_CHUNKS`, and
  `MAX_UPLOAD_BYTES` for local retrieval;
- `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, and `MAX_CHAT_CONTENT_BYTES` for web
  boundaries.
- `TRUST_PROXY_HEADERS` only when a trusted reverse proxy overwrites
  `X-Real-IP`; leave it false for direct backend access.

`CHROMA_DB_PATH` is a historical compatibility name. The current RAG store is
SQLite WAL plus serialized normalized embeddings in that directory; ChromaDB
is not required.

## Run locally

```bash
make dev
```

The backend listens on `127.0.0.1:8000`; Vite listens on
`127.0.0.1:3000` and proxies `/api/` to the backend. The local API docs are
available at `/docs` while `ENVIRONMENT=development`.

The model is loaded explicitly through the UI or:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/model/load
```

The first load may download a model and consume substantial memory. Do not
assume model download, inference speed, or provider availability in unit tests.

## Test and quality loop

Run the same blocking checks as CI:

```bash
make lint
make test
make security
make shellcheck
make docker-build
```

Useful focused commands from the repository root:

```bash
PYTHONPATH=backend pytest -c backend/pyproject.toml backend/tests/test_model_router.py
PYTHONPATH=backend pytest -c backend/pyproject.toml backend/tests/test_rag.py
cd frontend && npm test && npm run lint && npm run build
```

API tests should override the model and RAG dependencies so they do not
download models. Integration tests with real models/providers belong in an
isolated environment with explicit credentials and data handling approval.

## Code conventions

- Keep blocking llama.cpp, embedding, and remote HTTP operations out of the
  async event loop; use worker threads or an equivalent bounded executor.
- Validate all external input with Pydantic and preserve configured bounds.
- Keep provider credentials and raw upstream errors out of response models and
  logs.
- Preserve local fallback and SSE framing when changing routing.
- Keep frontend API calls same-origin by default and do not introduce unsafe
  HTML sinks or browser-side provider credentials.
- Add a regression test before fixing a bug; run the focused red test, make the
  smallest safe change, then run the relevant full suite.

## Docker validation

```bash
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:8000/api/v1/health
docker compose down
```

The backend container is non-root and read-only by design. Persistent model
and RAG volumes should not be replaced with broad host mounts in development
or production without reviewing ownership, backup, and data exposure.

## Pull request checklist

- [ ] Scope and API compatibility are documented.
- [ ] Tests cover new behavior and failure paths.
- [ ] Black, Flake8, mypy, pytest/coverage, frontend lint/test/build, audits,
      Compose validation, and Docker build pass.
- [ ] No secrets, model artifacts, local data, or generated dependencies are
      staged.
- [ ] Production claims are separated from local/CI evidence.
