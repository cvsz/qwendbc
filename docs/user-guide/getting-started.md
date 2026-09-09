# User Guide: Getting Started

QwenDBC provides a local-first chat interface for a Qwen GGUF model. Hosted
free-provider routing and local document retrieval are optional.

## Start the application

Prerequisites are Docker Compose v2.24+, at least 8 GB RAM, and enough storage
for the selected GGUF model and embedding cache.

```bash
cp configs/.env.example .env
make install
```

Open `http://localhost:3000`. The backend health endpoint is
`http://localhost:8000/api/v1/health`; development API docs are at
`http://localhost:8000/docs`.

Both ports bind to loopback by default. Keep `BACKEND_BIND_HOST` private; do
not expose `FRONTEND_BIND_HOST` publicly without the production controls in the
[deployment guide](../deployment/docker.md).

## Load and use a model

1. Open the control room and choose **Load local model**.
2. Wait for the model status to become loaded. The first load may download the
   configured GGUF model and can take time or significant memory.
3. Return to Chat, enter a message, and send it.
4. Use **Unload local model** when the host needs the memory for another task.

The model file and cache are stored in the Docker `model_data` volume and are
not tracked by Git.

## Free-model routing

Remote routing is disabled by default. To enable it for an authorized
deployment, configure the backend environment with a strong application token
and approved provider settings:

```dotenv
REMOTE_MODELS_ENABLED=true
QWENDBC_ACCESS_TOKEN=<inject-out-of-band>
FREE_PROVIDER_ORDER=kilo,opencode,openrouter,local
```

The application token is entered in the UI's **Operator access** field only
for the current browser session. Provider API keys remain backend-only and are
never bundled into the frontend. The catalog and chat surfaces show the
selected provider/model and whether fallback was used.

For production, also set `ENVIRONMENT=production`, explicit
`ALLOWED_ORIGINS`, explicit `ALLOWED_HOSTS`, and TLS/identity controls at the
edge. Production requires a token of at least 32 characters and disables API
documentation routes.

## Document retrieval

The Notes panel accepts UTF-8 text uploads within `MAX_UPLOAD_BYTES`. Enable
**Use local RAG** before sending a chat message to add the most relevant local
chunks to the request context. Documents can also be searched directly through
the API:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F 'file=@notes.txt;type=text/plain'

curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"deployment steps","top_k":5}'
```

When access is configured, add
`-H "Authorization: Bearer ${QWENDBC_ACCESS_TOKEN}"` to protected requests.
The RAG store is private SQLite WAL data under the `chroma_data` volume; treat
it as sensitive and back it up using a consistent SQLite-aware procedure.

## Themes and accessibility

The interface supports **Day**, **Night**, and **System** themes. System follows
the browser preference. Reduced-motion preferences suppress nonessential
transitions, and the controls are keyboard accessible.

## Privacy and safety

Do not put provider keys, application tokens, private model files, or sensitive
documents in issues, screenshots, frontend build variables, or Git. If remote
routing is enabled, review provider retention and terms before sending
confidential prompts. For security reporting, follow the repository
[security policy](../../SECURITY.md).

*Last updated: September 2026*
