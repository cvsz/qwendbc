# Architecture Overview

QwenDBC is a local-first FastAPI and React application. Docker Compose runs a
static React build behind Nginx and keeps the backend, model files, and local
RAG data in a private service boundary.

## Runtime topology

```text
Browser
  |
  v
External TLS / identity edge (production)
  |
  v
Nginx frontend :8080  -- /api/ -->  FastAPI backend :8000
                                      |
                    +-----------------+------------------+
                    |                                    |
                    v                                    v
             LLMService / llama.cpp              ModelRouter
             local GGUF model                   free providers (opt-in)
                    |
                    v
          SQLite WAL RAG store + sentence-transformers
```

The host publishes frontend and backend ports on `127.0.0.1` by default.
Nginx proxies `/api/` to the backend over the Compose network. A production
edge should publish only the frontend and keep the backend host port private.

## Repository structure

```text
backend/
  app/
    main.py                    app factory, middleware, lifespan
    routers/chat.py            health, model, catalog, chat, SSE routes
    routers/documents.py      upload and semantic search routes
    schemas/                   Pydantic request/config/response models
    services/llm_service.py   local GGUF lifecycle and inference
    services/model_router.py  free-provider selection and fallback
    services/remote_provider.py OpenAI-compatible provider adapters
    services/rag_service.py  SQLite persistence and cosine retrieval
    services/access_control.py bearer access and process-local limits
  tests/
frontend/
  src/                         React UI, API client, theme helpers
docker/
  Dockerfile.backend           non-root Python image
  Dockerfile.frontend          Vite build and Nginx runtime
  nginx.conf                   same-origin API proxy and browser headers
```

## Request flows

### Health and model lifecycle

`GET /api/v1/health` is intentionally lightweight and public for liveness. It
reports model state and non-secret routing state without triggering remote
catalog discovery. Model info/load/unload are protected when an application
token is configured and use worker threads for blocking model operations.

### Chat

1. FastAPI validates message count, content size, generation parameters, and
   optional provider/model selection.
2. Optional RAG retrieval runs in a worker thread and injects bounded context
   into the latest user message.
3. `ModelRouter` selects local inference or eligible free remote providers in
   configured order.
4. Remote calls use timeouts, non-blocking concurrency limits, normalized
   catalogs, and safe fallback errors.
5. The response includes non-secret `qwendbc` provider/model metadata. SSE
   streams preserve the `[DONE]` marker and only fall back before content is
   emitted.

### Document retrieval

Uploads accept UTF-8 text up to `MAX_UPLOAD_BYTES`. Text is normalized and
chunked, embeddings are generated lazily with the configured
`sentence-transformers` model, and chunks are stored in a private SQLite
database at `CHROMA_DB_PATH`. Search performs bounded in-process cosine
similarity over persisted embeddings; SQLite is not exposed as a network
service. The setting and volume retain their historical Chroma names for
configuration/data-path compatibility only; existing Chroma data requires a
reviewed re-index/migration and is not silently treated as empty.

## Security boundaries

The application factory configures explicit CORS methods/headers,
`TrustedHostMiddleware`, request bounds, defensive response headers, and
production-only configuration checks. Production requires a bearer token of
at least 32 characters, explicit hosts/origins, and `DEBUG=false`; API docs
routes are disabled.

Remote provider keys are backend-only and production provider endpoints must
use HTTPS. Free-provider catalogs reject paid automatic routes and non-text
modalities. A provider may still receive the
prompt when remote routing is enabled, so provider terms and data handling
must be reviewed before activation.

The backend image runs as a non-root user. Compose uses a read-only root
filesystem, dropped backend capabilities, no-new-privileges, process limits,
and isolated temporary filesystems. Model/cache and RAG volumes are persistent
and sensitive.

The application token is not an identity provider, RBAC system, tenant
boundary, immutable audit log, or distributed rate limiter. Production adds
those controls at the platform/edge layer when required.

## Lifecycle and concurrency

`LLMService` is a process singleton so one process does not load duplicate GGUF
models. `ModelRouter` instances are cached per LLM service, while provider
catalogs use a short in-process TTL. Blocking inference, embedding, and remote
HTTP work run outside the async event loop. Horizontal scaling requires shared
edge quotas, coordinated model/data ownership, and an explicit operational
strategy for SQLite volume access.

## Observability and recovery

Application logs record lifecycle and failure events but must be collected with
authorization headers, prompts, provider responses, and filesystem secrets
redacted at the edge/platform. Add metrics, tracing, alerts, SLOs, and an
immutable audit trail in production.

Model artifacts can be re-downloaded after provenance review. SQLite RAG data
requires encrypted, access-controlled backups and restore tests. Record commit
SHA, image digests, configuration revision, CI result, staging evidence, and
rollback verification for each release.

*Last updated: September 2026*
