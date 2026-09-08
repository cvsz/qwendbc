# QwenDBC Quick Start

## Docker (recommended)

Prerequisites: Docker Compose 2.24 or newer.

```bash
cp configs/.env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

Docker publishes both ports on `127.0.0.1` by default. Keep `BIND_HOST=127.0.0.1` unless you have an authenticated reverse proxy, VPN, zero-trust access layer, or equivalent network control. Setting `BIND_HOST=0.0.0.0` also exposes the frontend's `/api/` reverse proxy, not just the static UI.

The model is downloaded only when you click **Load Model** or call the model-load endpoint. The GGUF is stored in the Docker `model_data` volume and is not committed to Git.

Compose loads `configs/.env.example` and then the optional root `.env` into the backend container. This means generation/RAG settings in `.env` are honored in Docker; Compose only overrides container-internal host and data paths.

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

## Document retrieval

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F 'file=@notes.txt;type=text/plain'

curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"deployment steps","top_k":5}'
```

Only UTF-8 text uploads are supported by the current API. Nginx permits request bodies up to 100 MiB so the backend's lower `MAX_UPLOAD_BYTES` setting remains the authoritative application limit.

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

> The application has no built-in authentication. Do not expose either the backend or the frontend API proxy to an untrusted network without an authenticated reverse proxy or equivalent access control.
