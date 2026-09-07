# QwenDBC

QwenDBC is a local-first FastAPI + React application for running a GGUF Qwen model with `llama.cpp`, plus local document ingestion and semantic search with ChromaDB.

## Current stack

- Backend: Python 3.13, FastAPI 0.141.x, Pydantic v2, llama-cpp-python 0.3.35+
- Retrieval: ChromaDB 1.5.x, sentence-transformers 6.x
- Frontend: React 19.2, Vite 8.2
- Runtime: Docker Compose, Nginx frontend reverse proxy
- Quality: Black, Flake8, mypy, pytest/coverage, oxlint, ShellCheck when shell scripts exist
- Security: CodeQL, dependency review, pip-audit, npm audit, Dependabot

> **Security boundary:** this project does not implement authentication. Keep the backend private/local or put it behind an authenticated reverse proxy before exposing it to the Internet.

## Quick start with Docker

```bash
cp configs/.env.example .env
# Adjust N_THREADS and other settings if needed.
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs

The first model load downloads the configured GGUF file into the Docker `model_data` volume. The repository does **not** track local GGUF files or Hugging Face cache symlinks.

## Local development

Prerequisites: Python 3.13, Node.js 24, and standard build tools required by `llama-cpp-python`.

```bash
make setup
make dev
```

The Vite development server listens on port 3000 and proxies `/api/*` to the FastAPI backend on port 8000.

## Quality gates

```bash
make lint
make test
make security
make shellcheck   # reports "No tracked .sh files" until shell scripts are added
make docker-build
```

`make lint` is check-only; it no longer modifies source files. Use `make format` when you explicitly want Black to rewrite Python files.

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

- `MODEL_NAME`, `MODEL_FILE`, `MODEL_PATH`
- `N_THREADS`, `N_BATCH`, `MAX_CONTEXT_LENGTH`
- `CHROMA_DB_PATH`, `EMBEDDING_MODEL`, `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`
- `MAX_UPLOAD_BYTES`
- `ALLOWED_ORIGINS`

`.env`, model files, vector-store data, virtual environments, caches, and frontend build outputs are ignored by Git.

## CI behavior

CI is intentionally blocking. Python lint/type/test/security failures, frontend lint/build/audit failures, Compose validation, and Docker build failures now fail the workflow instead of being hidden behind `|| true` or `|| echo`.

The repository currently contains no tracked `.sh` scripts, so ShellCheck correctly reports that there is nothing to scan. The CI job becomes active automatically if shell scripts are added later.

## License

MIT
