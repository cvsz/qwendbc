# QwenDBC Quick Start

## Docker (recommended)

Prerequisites: Docker with Compose v2.

```bash
cp configs/.env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

The model is downloaded only when you click **Load Model** or call the model-load endpoint. The GGUF is stored in the Docker `model_data` volume and is not committed to Git.

## Local development

Prerequisites: Python 3.13, Node.js 24, GNU Make, and native build tools required by `llama-cpp-python`.

```bash
make setup
make dev
```

`make setup` creates `.venv`, installs backend development dependencies, installs frontend dependencies, and creates `.env` from `configs/.env.example` if needed.

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
```

Tune `N_THREADS` to the machine rather than blindly increasing it. Lower `MAX_CONTEXT_LENGTH` or use a smaller quantized model if memory pressure is high.

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

Only UTF-8 text uploads are supported by the current API.

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

In Docker, Nginx proxies `/api/` to the backend service. In local development, Vite proxies `/api/` to `http://localhost:8000`. Use `VITE_API_URL` only when a deployment intentionally needs a different API origin.

> The backend has no built-in authentication. Do not expose it directly to the public Internet without an authenticated reverse proxy or equivalent access control.
