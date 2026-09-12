# AI-DBC Production-Readiness Hardening Design

**Date:** 2026-09-12
**Scope:** Existing AI-DBC FastAPI/React/Docker application

## Objective

Make the current repository reproducible and production-ready without adding
new product capabilities or changing the public API. Preserve unrelated
uncommitted work already present in the worktree.

## Findings driving the work

- The checked-in local virtual environment is stale/broken because its Python
  interpreter points outside this repository; setup must not depend on it.
- The frontend control panel uses a separate request helper that does not share
  the bearer-token behavior of `frontend/src/api.js`, so protected model
  operations fail when access control is enabled.
- The control panel calls `/model/streaming`, but the backend exposes no such
  endpoint and streaming is a per-request chat option.
- Backend, frontend, Compose, CI, deployment files, and documentation need a
  single consistency pass so referenced behavior and quality gates match the
  implementation.

## Design

### API and frontend integration

Use the existing frontend API module as the single request boundary. Extend it
only as needed for model info, unload, and control-panel health operations, and
reuse session-scoped operator-token handling. Remove the unsupported streaming
toggle UI or replace it with an accurate per-chat streaming control only if the
existing chat contract supports it without an API change. Keep error handling
safe and consistent.

### Backend behavior and regression coverage

Preserve the existing OpenAI-compatible completion and SSE endpoints. Add tests
for protected lifecycle/catalog/document operations, request-level streaming,
remote/local route validation, and the control-panel-facing model-info/unload
paths. Tests must use dependency injection or fakes rather than loading a real
model or contacting providers.

### Reproducibility and upgrades

Repair setup assumptions without tracking environments or generated artifacts.
Review runtime and development dependency pins/ranges, frontend lockfile
consistency, Python/Node version declarations, and Docker build inputs. Upgrade
only compatible versions supported by the project and verify with install,
lint, tests, audits, and build checks. Do not copy credentials or machine-local
model files into the repository.

### Deployment, CI, and documentation

Validate all Compose variants and workflow references. Add only missing files
that are required by existing repository promises (for example, a referenced
workflow/configuration file), and keep workflow permissions and failure modes
explicit. Update README, quickstart, API, deployment, security, and user-guide
text where the final behavior differs. Keep local defaults loopback-only and
production safeguards intact.

## Error handling and security

Protected endpoints continue to require the configured bearer token. Provider
credentials remain server-side. No endpoint will expose secrets, local paths,
or raw provider errors. Model and RAG operations remain off the event loop.
Streaming must release remote capacity on success, failure, and disconnect.

## Verification gates

Run the strongest available local checks in this order:

1. Backend formatting, lint, type checking, and tests.
2. Frontend tests, lint, and production build.
3. Dependency audits where network/package tooling is available.
4. Compose config validation and Docker builds where Docker is available.
5. A final diff review, whitespace check, and repository-reference scan.

Environment/tooling failures will be reported separately from code failures.
