# AI-DBC Security Overview

This document is the deployment-facing security contract for AI-DBC. It
describes controls present in the repository and the controls that remain the
responsibility of the operator.

## Security model

AI-DBC is local-first. The default Compose configuration binds published
ports to loopback and keeps hosted model providers disabled. A production
deployment must add an authenticated edge, TLS, explicit host/origin policy,
secret injection, monitoring, and tested backups.

```text
Browser / operator
        |
        v
TLS + identity-aware edge (operator responsibility)
        |
        v
Nginx static UI + same-origin /api proxy
        |
        v
FastAPI: host/CORS checks, bearer access, bounds, routing limits
        |                         |
        v                         v
Local llama.cpp model       SQLite WAL + local embeddings
        |
        v
Optional allowlisted free-provider APIs
```

The application token is a shared application boundary. It is not a user
directory, SSO integration, role system, tenant boundary, or immutable audit
trail.

## Access control

Development can run with an empty `QWENDBC_ACCESS_TOKEN` for local testing. If
the token is configured, chat, model lifecycle/info, model catalog/refresh,
and document upload/search routes require:

```http
Authorization: Bearer <application-token>
```

The health and root endpoints remain readable for liveness and basic service
discovery. Production configuration rejects an empty token and requires at
least 32 characters. Generate and inject it out of band; do not put it in Git,
the frontend bundle, a URL, or a browser-persisted setting.

Authentication uses constant-time token comparison. The in-process limiter
keys accounting by a hash of the token and the client address, so raw tokens
are not used as map keys or logged. Compose enables `TRUST_PROXY_HEADERS` only
for the backend behind the repository Nginx proxy, which overwrites
`X-Real-IP`; direct deployments must leave it disabled unless their proxy is
equally trusted. The limiter is process-local and fixed window; a multi-instance
deployment must enforce shared quotas at the edge.

## Request and response safety

Pydantic validation bounds message count/content, aggregate UTF-8 chat bytes,
generation parameters, document query size, retrieval count, upload size, and
the total local RAG chunk quota. Embeddings are generated in bounded batches.
Remote calls have explicit timeouts, a non-blocking concurrency limit, and
provider fallback behavior. Upstream exceptions are mapped to safe public
messages; credentials, raw upstream bodies, and internal paths are not part of
normal API responses.

The application configures explicit CORS methods and headers with credentials
disabled. `TrustedHostMiddleware` rejects hosts outside `ALLOWED_HOSTS`.
Production disables `/docs`, `/redoc`, and `/openapi.json`. Application and
Nginx layers emit defensive headers including CSP, frame denial, MIME sniffing
protection, referrer policy, and permissions policy.

Streaming responses preserve SSE framing and only fall back to another model
before the first content chunk. Operators should still apply edge timeouts,
connection limits, and abuse controls for long-lived streams.

## Model and provider boundary

Remote routing is opt-in through `REMOTE_MODELS_ENABLED`. Only normalized free
text-capable catalog entries are eligible; paid automatic routes and unrelated
modalities are rejected. Provider API keys are read only by the backend and
are never accepted from the browser. Review each provider's terms, retention,
quotas, and data handling before enabling it for sensitive prompts.

Downloaded GGUF and embedding models are executable supply-chain inputs. Pin or
review their source and checksum through the deployment process. Production
configuration requires lowercase 40-character Hugging Face commit revisions
for both model artifacts, a matching `MODEL_SHA256` for the GGUF, and HTTPS
for configured remote provider endpoints. Restrict write access to model
volumes and do not load untrusted model repositories.
The application does not claim that a free-provider label guarantees zero
cost, availability, privacy, or suitability for regulated data.

## Data protection

Uploaded text, SQLite RAG chunks, embeddings, local model files, caches, and
provider responses can contain sensitive or proprietary information. The RAG
store uses SQLite WAL files under `CHROMA_DB_PATH` (the setting name is kept
for compatibility) and is not exposed as a network service. Protect the
`chroma_data` and `model_data` volumes with host permissions and encrypted
storage. Backups must be encrypted, access-controlled, retention-limited, and
periodically restored in a non-production environment.

The repository intentionally ignores `.env`, model files, caches, and data
directories. If a credential has ever entered Git history, rotate/revoke it;
deleting it from the working tree is not sufficient.

## Container and network controls

The backend image runs as a non-root `app` user. Compose gives it a read-only
root filesystem, drops Linux capabilities, disables privilege escalation,
limits process count, and provides only `/tmp`, model/cache, and RAG storage
as writable locations. The frontend root filesystem is also read-only with
the temporary Nginx paths supplied as tmpfs.

Keep the backend host port private. If changing `FRONTEND_BIND_HOST` from its
loopback default, use a firewall and an authenticated TLS reverse proxy. Keep
`BACKEND_BIND_HOST` loopback/private. Configure the
edge with HSTS, request-size limits no larger than the application contract,
connection/request rate limits, access logs with sensitive headers redacted,
and a health-check policy that does not expose protected data.

## Operations and residual risk

The repository runs Python and frontend dependency audits, CodeQL,
dependency-review, lint, type checking, tests, frontend build/audit, and
Compose image builds in CI. A green local run does not prove that hosted CI,
image scanning, signed releases, external TLS, provider contracts, backups,
or runtime SLOs have been validated.

`llama-cpp-python` currently requires `diskcache` at import time. The current
`diskcache 5.6.3` advisory has no upstream fix in the resolver used by this
repository. AI-DBC does not instantiate `LlamaDiskCache`; the backend runs as
non-root with read-only root storage and writable data volumes restricted to
the application. CI and `make security` therefore ignore only
`PYSEC-2026-2447`, explicitly and temporarily. Re-evaluate this exception
before every LLM dependency update and remove it when a fixed release exists.

The following are intentionally not implemented in this application and must
be supplied when required by the deployment risk profile:

- centralized identity, SSO, RBAC, tenant isolation, and per-user audit;
- distributed rate limiting, quotas, WAF, DDoS protection, and abuse response;
- TLS termination and certificate lifecycle;
- centralized secret management, rotation, and revocation workflows;
- immutable audit logging, metrics, tracing, alerting, and on-call runbooks;
- high availability, automated failover, and disaster-recovery objectives;
- organization-specific privacy, retention, residency, and compliance review.

## Production release checklist

- [ ] `ENVIRONMENT=production` and `DEBUG=false`.
- [ ] A random `QWENDBC_ACCESS_TOKEN` with at least 32 characters is injected
      outside the repository.
- [ ] GGUF and embedding revisions are immutable; `MODEL_SHA256` matches the
      exact approved GGUF bytes.
- [ ] `ALLOWED_HOSTS` and `ALLOWED_ORIGINS` contain only required values.
- [ ] Remote providers are disabled unless approved and separately configured.
- [ ] TLS and identity-aware edge access are active; backend port is private.
- [ ] Host and volume permissions are restricted; model/RAG backups are
      encrypted and a restore test is recorded.
- [ ] CI passed on the exact commit, including dependency and image audits.
- [ ] Runtime health, logs, metrics, rate-limit behavior, and rollback have
      been tested in staging.
- [ ] Data retention and provider handling have been approved for the prompts
      and documents that will be processed.

## Reporting

See the repository [security policy](../../SECURITY.md) for private
vulnerability-reporting guidance. Do not put credentials, private data, or
exploit details in a public issue.
