# Troubleshooting

Use read-only diagnostics first. Do not remove Docker volumes, containers, or
host directories on a production system until a verified backup and rollback
plan exist.

## Check service state

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
curl -i http://127.0.0.1:8000/api/v1/health
```

The health endpoint should return `200` and JSON. It does not load the model or
refresh remote provider catalogs.

## Backend does not start

Inspect the logs for configuration validation errors. Common causes include:

- `ENVIRONMENT=production` without a 32-character application token;
- wildcard/empty `ALLOWED_HOSTS` or wildcard production CORS origins;
- `MAX_TOKENS` greater than `MAX_CONTEXT_LENGTH`;
- production model revisions/checksum are missing or the container health probe
  uses a Host value that is not in `ALLOWED_HOSTS`;
- an invalid provider order that does not end with `local`;
- insufficient permissions on the model or RAG volumes.

Validate the rendered Compose file without printing secret values:

```bash
docker compose config --quiet
docker compose config --services
```

## Frontend cannot reach the API

In Docker, the browser calls the frontend origin and Nginx proxies `/api/` to
the backend service. Confirm both services are healthy and inspect the
frontend logs. In local development, Vite proxies to
`http://127.0.0.1:8000`.

Open WebUI is a separate Compose service on port `3001`. Its upstream must be
`http://backend:8000/api/v1` from inside Compose; using `localhost:8000` from
the Open WebUI container points back to Open WebUI itself. Confirm the
`open_webui_data` volume is mounted and that `OPENAI_API_KEYS` matches the
AI-DBC application token when access control is enabled.

If a browser reports a CORS or Host error, check that the public origin appears
exactly in `ALLOWED_ORIGINS` and the incoming host appears in `ALLOWED_HOSTS`.
Do not solve this by enabling `*` in production.

## Protected route returns 401

Confirm the token is present in the backend environment without printing its
value and send the exact value as:

```http
Authorization: Bearer <application-token>
```

Do not put the token in a URL or commit it. If the token may have leaked,
rotate it in the secret system and invalidate the relevant edge session.

## Rate limit returns 429

The application applies a process-local fixed-window limit when access is
configured. Remote provider calls also have a bounded non-blocking semaphore.
Respect `Retry-After`, reduce client concurrency, and inspect edge limits.
For multiple replicas, configure distributed quotas at the edge; changing the
application setting on one process does not coordinate the others.

## Model load fails

```bash
docker compose logs --tail=200 backend
docker system df
docker compose exec backend sh -c 'id && df -h /app/models /tmp'
```

Check model name/file compatibility, available memory/storage, network access
for the first download, and host permissions. The model is loaded explicitly;
normal health checks do not download it. Avoid loading unreviewed model
repositories.

## Chat fails or falls back

Inspect the response's non-secret `ai-dbc` metadata. Automatic routing tries
the configured free-provider order and ends at local fallback. Providers may
be unavailable because credentials are absent, the catalog has no eligible
free text model, the request timed out, or a provider returned a retryable
failure.

To isolate local inference, set and restart with:

```dotenv
MODEL_MODE=local
REMOTE_MODELS_ENABLED=false
```

When streaming, a provider fallback is only possible before the first content
chunk. A completed SSE response ends with `data: [DONE]`.

## Document upload/search fails

Only UTF-8 text is accepted. Check file size against `MAX_UPLOAD_BYTES` and
inspect the backend logs for embedding initialization errors. The RAG service
is lazy and stores SQLite WAL data under `CHROMA_DB_PATH`; the historical
setting/volume name does not mean ChromaDB is installed.

```bash
docker compose exec backend sh -c 'ls -la /app/chroma_db'
```

Do not edit or delete the SQLite database while the service is running. For
corruption or migration work, take a consistent backup, stop the backend, and
use a SQLite-aware recovery procedure.

## Performance and capacity

Review host CPU, memory, disk, and container process limits. Tune
`N_THREADS`, `N_BATCH`, `MAX_CONTEXT_LENGTH`, `MAX_TOKENS`, and the configured
remote concurrency limit for the machine. One process owns one local model;
horizontal scaling requires a deliberate model/volume and shared-quota design.

Long-lived SSE requests require appropriate edge read timeouts and connection
limits. Do not increase timeouts or body limits blindly on a public edge.

## Safe recovery

For a reversible restart:

```bash
docker compose restart backend frontend
docker compose ps
curl --fail http://127.0.0.1:8000/api/v1/health
```

For a release rollback, redeploy the previously recorded image digest and
configuration revision. Preserve the model and RAG volumes unless the
recovery plan explicitly calls for a verified restore.

## Information to collect for support

Provide the commit/image identifiers, sanitized configuration keys and values,
service status, relevant redacted logs, host OS/runtime versions, memory/disk
availability, and exact reproduction steps. Remove tokens, provider keys,
prompts, uploaded documents, model paths that reveal sensitive layout, and
personal data before sharing.

For vulnerabilities, use the private process in
[SECURITY.md](../../SECURITY.md), not a public issue.

*Last updated: September 2026*
