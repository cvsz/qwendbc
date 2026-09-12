# AI-DBC Quick Start

## Docker (recommended)

Prerequisites: Docker Compose 2.24 or newer.

```bash
make install
```

This creates `.env` from `configs/.env.example` when needed, builds both
services, starts the full stack, and waits for the health checks. Remote
providers remain disabled until you explicitly configure them. Use
`make docker-down` to stop it. The lower-level equivalent remains:

```bash
cp configs/.env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

Docker publishes both ports on `127.0.0.1` by default. Keep
`BACKEND_BIND_HOST=127.0.0.1` so the backend remains private. If an edge needs
to reach the UI, set only `FRONTEND_BIND_HOST` and keep the backend port on a
loopback/private interface.

If ports 8000 or 3000 are already occupied, use for example
`make install BACKEND_HOST_PORT=8100 FRONTEND_HOST_PORT=3100`.

The model is downloaded only when you click **Load local model** or call the model-load endpoint. The GGUF is stored in the Docker `model_data` volume and is not committed to Git.

Compose loads `configs/.env.example` and then the optional root `.env` into the backend container. This means generation/RAG settings in `.env` are honored in Docker; Compose only overrides container-internal host and data paths.
The backend container runs without root privileges and with a read-only root filesystem. The `model_data` and `chroma_data` volumes hold the model/cache and SQLite RAG data respectively.

## Local development

Prerequisites: Python 3.13, Node.js 24, GNU Make, and native build tools required by `llama-cpp-python`.

```bash
make setup
make dev
```

`make setup` creates `.venv`, installs backend development dependencies, installs frontend dependencies, and creates `.env` from `configs/.env.example` if needed. Development servers bind to loopback by default.

Run the quality gates before committing:

```bash
make lint
make test
make security
make shellcheck
make docker-build
```

## First model load

```bash
curl -X POST http://localhost:8000/api/v1/model/load
```

The default model is `Qwen/Qwen2.5-1.5B-Instruct-GGUF` with the Q4_K_M GGUF. Initial download and load time depends on your network, CPU, memory, and storage; the project does not promise a fixed duration or token rate.

For CPU-only systems, start with:

```dotenv
N_THREADS=4
MAX_CONTEXT_LENGTH=4096
N_BATCH=512
MAX_TOKENS=2048
```

`MAX_TOKENS` must not exceed `MAX_CONTEXT_LENGTH`. Tune `N_THREADS` to the machine rather than blindly increasing it. Lower `MAX_CONTEXT_LENGTH` or use a smaller quantized model if memory pressure is high.

## Chat example

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":128}'
```

## Free-model routing

The safe default is local-compatible `MODEL_MODE=auto_free` with
`REMOTE_MODELS_ENABLED=false`. To enable hosted free routing, set a strong
application token and authorized provider settings in the root `.env`:

```dotenv
REMOTE_MODELS_ENABLED=true
QWENDBC_ACCESS_TOKEN=replace-with-an-operator-token
FREE_PROVIDER_ORDER=kilo,opencode,openrouter,local
```

Never copy provider keys into the frontend or commit them. AI-DBC reads the
project `.env` and process environment only; it never loads the shared
`.env.ai` operator reference. The frontend's **Operator access** field stores
the application token only in the current browser session.

Inspect the eligible catalog:

```bash
curl http://localhost:8000/api/v1/models
```

Authorized chat and catalog refresh requests use the bearer token:

```bash
curl -X POST http://localhost:8000/api/v1/models/refresh \
  -H "Authorization: Bearer ${QWENDBC_ACCESS_TOKEN}"

curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer ${QWENDBC_ACCESS_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hello"}],"use_rag":false}'
```

Automatic fallback follows `kilo,opencode,openrouter,local`. Only free text
models are eligible, and the response reports its selected provider/model in
`ai-dbc` metadata. Set `MODEL_MODE=local` or
`REMOTE_MODELS_ENABLED=false`, then restart, to roll back remote routing.

For a production configuration, set an explicit public origin and host, keep
`DEBUG=false`, and use a randomly generated token of at least 32 characters:

```dotenv
ENVIRONMENT=production
ALLOWED_ORIGINS=https://chat.example.com
ALLOWED_HOSTS=chat.example.com
QWENDBC_ACCESS_TOKEN=generate-and-inject-this-out-of-band
MODEL_REVISION=pin-a-40-character-hugging-face-commit
EMBEDDING_MODEL_REVISION=pin-a-40-character-hugging-face-commit
MODEL_SHA256=pin-a-64-character-model-file-digest
```

Production disables the FastAPI documentation routes and rejects unknown Host
headers. Terminate TLS at the edge and keep the backend port private. The
revision values must be lowercase 40-character immutable commits, and
`MODEL_SHA256` must be the exact lowercase SHA-256 digest of the GGUF file.
Production provider endpoints must use HTTPS.

The web interface persists **Day**, **Night**, or **System** theme selection;
System follows the browser preference and reduced-motion settings are honored.

## Document retrieval

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F 'file=@notes.txt;type=text/plain'

curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"deployment steps","top_k":5}'
```

Only UTF-8 text uploads are supported by the current API. Nginx rejects bodies
above 6 MiB before multipart parsing, while the backend's lower
`MAX_UPLOAD_BYTES` setting (5 MiB maximum) remains authoritative. The local
SQLite store is initialized lazily and should be included in encrypted, tested
backups.

## Troubleshooting

### Backend does not start

```bash
docker compose logs backend
```

For local development, verify Python 3.13 is active and rerun `make setup-backend`.

### Model load fails

- Verify network access for the first Hugging Face download.
- Verify free memory and storage.
- Check `MODEL_NAME` and `MODEL_FILE` in `.env`.
- Check backend logs for the actual exception.

### Frontend cannot reach the API

In Docker, Nginx proxies `/api/` to the backend service. In local development, Vite proxies `/api/` to `http://127.0.0.1:8000`. Use `VITE_API_URL` only when a deployment intentionally needs a different API origin.

The production Nginx policy permits same-origin API calls by default. If a
deployment builds with an external `VITE_API_URL`, update the edge/browser CSP
`connect-src` allowlist to that exact HTTPS origin.

> When `QWENDBC_ACCESS_TOKEN` is set, protected API calls require a bearer token. Production always requires that token. Do not expose either the backend or the frontend API proxy to an untrusted network without TLS, the application token, and an authenticated reverse proxy or equivalent access control.
