# Security Policy

## Supported version

Security fixes are applied to the current `main` branch and the latest published release when practical. Older releases may not receive backports.

## Reporting a vulnerability

**Do not publish exploit details, credentials, private data, or reproduction steps in a public issue.**

Use GitHub's **Private Vulnerability Reporting** for this repository when the **Report a vulnerability** option is available under the Security tab. If private reporting is not enabled, open a public issue containing only a request for a private maintainer contact channel; do not include sensitive technical details in that issue.

A valid private report should include:

- affected version or commit;
- affected component and preconditions;
- impact assessment;
- minimal reproduction steps or proof of concept;
- suggested mitigation, if known.

Do not assume a specific response or remediation deadline unless a maintainer explicitly confirms one for the report.

## Current security boundary

AI-DBC is designed primarily for local/private use. The application currently provides:

- Pydantic request and configuration validation, including bounded message,
  upload, generation, and retrieval parameters;
- explicit CORS origins and `TrustedHostMiddleware` host validation;
- optional bearer-token protection for chat, model lifecycle, catalog, and
  document routes; production configuration requires a non-empty token of at
  least 32 characters;
- a process-local fixed-window request limit and bounded remote-provider
  concurrency;
- free text-model allowlisting and provider-key isolation on the backend;
- local model execution and a private SQLite WAL-backed RAG store;
- loopback-only Docker and development bind defaults;
- non-root backend containers, read-only container root filesystems, dropped
  backend capabilities, and security headers in the application/Nginx layers;
- CodeQL, dependency review, Dependabot, `pip-audit`, and `npm audit` automation;
- local secret handling guidance through an ignored `.env`.

The application now centralizes request identity in an explicit local
`PrincipalContext` used by Cowork and the access-control boundary. This keeps
the existing single-owner principal namespace stable and ignores caller-supplied
tenant/role headers. It is still **not** a centralized identity provider,
multi-user RBAC system, or production tenant-isolation layer.

The application **does not currently implement** verified OIDC/JWT tenant
identity, distributed rate limiting, an immutable audit log, secret-manager
integration, TLS termination, HA/failover, or a hosted backup service. The
process-local token remains an application access boundary, not a replacement
for organization-wide identity and authorization.

Docker uses loopback-only `BACKEND_BIND_HOST` and `FRONTEND_BIND_HOST` defaults.
For remote access, terminate TLS
at an authenticated reverse proxy, VPN, or zero-trust access layer; set
`ENVIRONMENT=production`, explicit `ALLOWED_ORIGINS` and `ALLOWED_HOSTS`, and a
strong `QWENDBC_ACCESS_TOKEN`; keep the backend port private. Do not treat the
local rate limiter as sufficient protection for a horizontally scaled
deployment—enforce limits at the edge as well.

## Secret handling

Never commit `.env`, API keys, access tokens, private keys, or other credentials. If a real credential was committed at any point, removing it from the latest tree is insufficient: rotate/revoke the credential and assess whether Git history must be rewritten.

Local GGUF models, SQLite RAG data, embedding caches, and provider responses
may contain sensitive or proprietary information and are intentionally ignored
by Git. Protect the Docker volumes and include the RAG directory in encrypted,
access-controlled backups with restore tests.

## Dependency and model supply chain

- Review Dependabot and dependency-review findings before merging updates.
- Keep lockfiles committed where the ecosystem supports them and review
  dependency audit output before release.
- Review model repository provenance before changing `MODEL_NAME` / `MODEL_FILE`.
- Treat downloaded models and embedding models as third-party supply-chain artifacts.
- Production requires immutable model revisions and an exact `MODEL_SHA256`
  digest for the GGUF file; production remote endpoints must use HTTPS.
- Do not enable remote providers without reviewing their terms, data handling,
  quotas, and failure behavior.
- The current `diskcache` advisory is an explicitly documented exception for
  the mandatory `llama-cpp-python` import-time dependency; AI-DBC does not
  enable its disk cache. Re-evaluate and remove the audit ignore when upstream
  publishes a fix.
- Do not treat a workflow as validated when GitHub Actions is disabled or no workflow run exists for the commit.

## Security-related pull requests

Public pull requests may contain fixes **after** sensitive exploit details have been removed or coordinated privately. Do not embed secrets, active exploit payloads, or private-report content in public commits or CI logs.
