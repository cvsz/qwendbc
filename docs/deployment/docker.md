# Docker Deployment

This is the supported production-shaped Docker Compose deployment. It runs
the React build behind Nginx and keeps the FastAPI backend on the internal
Compose network. The default host bindings are loopback-only.

## Prerequisites

- Docker Engine with Compose v2.24 or newer;
- a host with enough memory and disk for the GGUF model and embedding cache;
- an external TLS and identity-aware edge for any non-local deployment;
- an approved secret-injection mechanism for the application/provider tokens.

## Production configuration

Create a root `.env` from the non-secret example, then replace the production
values through the deployment secret/configuration system:

```bash
cp configs/.env.example .env
```

At minimum, production requires:

```dotenv
ENVIRONMENT=production
DEBUG=false
BACKEND_BIND_HOST=127.0.0.1
FRONTEND_BIND_HOST=127.0.0.1
ALLOWED_ORIGINS=https://chat.example.com
ALLOWED_HOSTS=chat.example.com
QWENDBC_ACCESS_TOKEN=<inject-a-random-token-of-at-least-32-characters>
MODEL_REVISION=<40-character-immutable-hugging-face-commit>
EMBEDDING_MODEL_REVISION=<40-character-immutable-hugging-face-commit>
MODEL_SHA256=<64-character-sha256-of-the-exact-gguf-file>
REMOTE_MODELS_ENABLED=false
```

Use the actual public hostname in both allowlists. Keep
`REMOTE_MODELS_ENABLED=false` unless the provider terms, data handling,
quotas, credentials, and fallback behavior have been approved. Provider keys
belong only in the backend secret store; never place them in frontend build
variables.

Production requires lowercase 40-character Hugging Face commit revisions for
both the GGUF and embedding model plus a 64-character SHA-256 digest for the
exact GGUF bytes. Resolve and review those immutable references before
deployment; mutable branches and tags are rejected by configuration. Remote
provider endpoints must use HTTPS in production.

Compose deliberately overrides `HOST`, `PORT`, `MODEL_PATH`, and
`CHROMA_DB_PATH` with container values. The historical `CHROMA_DB_PATH` name
now points to a directory containing the private SQLite RAG database and its
WAL files. Existing Chroma data is not auto-migrated: the service detects a
legacy `chroma.sqlite3` store and requires a reviewed re-index/migration.
`RAG_EMBED_BATCH_SIZE` bounds embedding work per batch and
`MAX_RAG_CHUNKS` provides a hard local index quota; tune both to the host's
memory and storage budget.

## Build and start

Run the release gates on the exact commit intended for deployment before
building images:

```bash
make lint
make test
make security
make shellcheck
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose ps
```

Verify liveness without exposing protected data:

```bash
curl --fail http://127.0.0.1:8000/api/v1/health
curl --fail http://127.0.0.1:3000/
```

In production, also verify that `/docs`, `/redoc`, and `/openapi.json` return
404, an unknown Host is rejected, and protected routes return 401 without the
application token. Record the exact image digests, commit SHA, configuration
revision, and verification output in the release system.

## Container controls

The backend image runs as the non-root `app` user. Compose configures a
read-only root filesystem, drops backend capabilities, disables privilege
escalation, limits process count, and provides a no-exec temporary filesystem.
Only the model/cache and RAG volumes are persistent writable locations. The
frontend filesystem is also read-only; Nginx runtime, cache, log, and temp
paths are tmpfs mounts.

Do not add host mounts for the repository, `.env`, private keys, or arbitrary
host paths. Do not publish the backend port publicly. If a host bind must be
changed, set only `FRONTEND_BIND_HOST` behind an edge firewall and
authenticated TLS proxy; retain `BACKEND_BIND_HOST=127.0.0.1` or another
private interface.

## TLS edge contract

The Compose stack terminates HTTP only. The external edge must provide:

- certificate issuance and renewal;
- HSTS after HTTPS has been verified;
- identity-aware access and revocation;
- distributed request/concurrency limits and upload limits;
- redacted access logs, metrics, tracing, and alerting;
- forwarding of `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto` headers.

Example reverse-proxy shape:

```nginx
server {
    listen 443 ssl http2;
    server_name chat.example.com;

    # Supply certificates and TLS policy from the edge's managed config.
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 900s;
    }
}
```

The example is a shape, not a complete TLS policy. Review cipher suites,
certificate paths, access policy, body limits, and log redaction with the
platform team.

## Storage and backups

`model_data` stores the GGUF model and embedding/model cache. `chroma_data`
stores the SQLite RAG database despite its historical volume name. Treat both
as sensitive. Use encrypted host storage, restricted Docker/host access, and
retention-limited backups.

SQLite backups must be consistent with WAL mode. Prefer the SQLite online
backup API or stop the backend before taking an offline volume snapshot. A
generic operational sequence is:

```bash
docker compose stop frontend backend
# Snapshot the named chroma_data and model_data volumes with the platform backup tool.
docker compose start backend frontend
```

Record backup success, size/checksum, retention, and a periodic restore test.
Do not delete the live volume as part of a backup or troubleshooting command.

## Rollback and incident response

To disable hosted routing without changing local RAG data, set:

```dotenv
MODEL_MODE=local
REMOTE_MODELS_ENABLED=false
```

Restart the backend and verify health and an authorized local chat. If an
application token is exposed, revoke/rotate it in the secret system and
invalidate the affected edge session. If a provider key or model artifact is
exposed, revoke/rotate the credential and assess downloaded-data retention.
See [the security policy](../../SECURITY.md) for private reporting guidance.

## Release evidence boundary

Local Compose health and CI prove repository/image gates only. They do not
prove hosted DNS, TLS, identity, edge policy, signed image provenance,
provider availability, backup restoration, capacity, SLOs, or compliance.
Those must be verified and recorded in the target environment before calling
the deployment production-ready.
