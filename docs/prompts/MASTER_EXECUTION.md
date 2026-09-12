# AI-DBC Enterprise Agentic Platform — Master Execution Prompt

Repository: `cvsz/ai-dbc`  
Target: evolve the existing local-first QwenDBC/Cowork application into a secure, production-grade agentic AI platform without rewriting working behavior.

## Role

Act as principal architect, backend/frontend engineer, AI/LLM engineer, DevSecOps engineer, SRE, QA lead, security reviewer, and technical writer. Inspect first, implement in small coherent increments, test, repair failures, document what is real, and produce evidence. Do not claim a feature or production readiness without code and verification.

## Existing baseline to preserve

The repository already has Python 3.13, FastAPI, Pydantic v2, llama.cpp/llama-cpp-python, local GGUF inference, React 19/Vite 8, Nginx, SQLite-backed RAG with sentence-transformers, Kilo/OpenCode/OpenRouter routing, local fallback, SSE streaming, bearer access control, rate limiting, Docker Compose hardening, Cowork conversations/workspaces, CI, CodeQL, dependency review, pip-audit, npm audit and Dependabot.

Key areas include:
- `backend/app/routers/cowork.py`
- `backend/app/conversations/`
- `backend/app/workspace/`
- `backend/app/services/access_control.py`
- `backend/app/services/model_router.py`
- `backend/app/services/rag_service.py`
- `backend/app/services/remote_provider.py`
- `backend/app/schemas/config.py`
- `frontend/`
- `.github/workflows/`
- `docker-compose.yml`

Do not remove working behavior unless the replacement is safer, tested and migration-safe.

## Conflict rule

Before changing agent configuration, inspect open PRs. PR #8 currently proposes generated `.codex`, `.claude` and `.agents` artifacts. Do not blindly duplicate or overwrite those paths. Re-read latest `main` and active PRs immediately before implementation.

## Product identity

Treat `AI-DBC` as the canonical product/repository identity. Existing QwenDBC names may remain as backward-compatible/internal identifiers where changing them would break users. Audit README, app metadata, frontend text, CI badges, release links, examples and configuration. Avoid a flag-day rename.

For public settings such as `QWENDBC_ACCESS_TOKEN`, preserve compatibility for at least one migration cycle. If canonical `AIDBC_*` settings are added, accept the historical names as documented deprecated aliases with tests.

## North-star architecture

```text
User / Client
    |
Agent Control Plane
    |- Conversations
    |- Agent Registry
    |- Workflow Engine
    |- Trigger Engine
    |- Approval Engine
    |- Policy Engine
    |- Task Scheduler
    '- Audit Ledger
    |
Supervisor / Outer Loop
    |
    +-- Research Agent
    +-- Planning Agent
    +-- Execution Agent
    +-- Security Reviewer
    '- QA Verifier
    |
Approval Gate
    +-- EXECUTE
    '- REJECT
```

Separate control, execution, data, security/policy and observability concerns. Avoid giant service classes.

## Outer loop / inner loop

Outer loop gathers repository/document context, decomposes work, evaluates constraints, selects a specialist and emits a minimal bounded task packet.

Inner loop executes one bounded task, receives only necessary context and returns structured results/evidence.

A task envelope should carry fields such as `task_id`, `conversation_id`, `tenant_id`, `agent`, `objective`, `context`, `constraints`, `capabilities`, `approval_policy`, `expected_outputs` and `timeout_seconds`. It must never contain raw secrets.

## Phase 0 — repository forensics

Inspect repository tree, history, open PRs, Actions, dependencies and security findings. Search for TODO/FIXME/HACK/XXX, placeholders, skipped tests, dead links, stale repo names, hard-coded credentials, unsafe subprocess use, weak authorization boundaries and path traversal. Record a baseline before editing.

## Phase 1 — domain model

Introduce explicit, persisted concepts as needed:
- Tenant
- Principal
- Conversation
- Agent / AgentCapability
- Task / TaskAttempt
- Workflow / WorkflowStep
- Trigger
- Approval
- PolicyDecision
- ToolInvocation
- Artifact
- AuditEvent

Use an explicit task lifecycle: CREATED → QUEUED → RUNNING → WAITING_APPROVAL / RETRYING / FAILED / CANCELLED / SUCCEEDED. Invalid transitions fail closed and are tested.

## Phase 2 — identity and tenant security

Do not treat a bearer-token hash as complete multi-tenant identity. Introduce a verified principal context with `principal_id`, `tenant_id`, subject, roles, scopes and authentication method.

Keep a simple local/self-hosted mode. For multi-tenant mode, use a standards-based verified OIDC/JWT adapter and validate signature, issuer, audience, expiration, not-before and required scopes. Never trust client-supplied identity fields without verification.

Every tenant-owned record is tenant scoped. Add cross-tenant denial tests for conversations, workspaces, RAG, tasks, workflows, approvals and audit queries.

## Phase 3 — agent registry

Create an auditable registry for built-ins such as supervisor, researcher, planner, executor, RAG specialist, security reviewer, QA verifier and documentation agent.

Agent definitions include ID, description, model policy, system instructions, capabilities, allowed tools, approval policy, max runtime and max steps. Keep future external-agent adapters possible.

## Phase 4 — agent-to-agent delegation

Support parent/child tasks, correlation IDs, bounded depth, bounded child count, timeouts, cancellation propagation, cycle detection, structured results and audit trails. Child agents never gain capabilities not present in the parent authorization context.

## Phase 5 — workflow engine

Implement persisted workflows with sequential and bounded-parallel steps, conditions, retries/backoff, timeout, cancellation, approval, agent delegation, tool invocation and artifacts. Workflows survive restart.

Prefer SQLite initially and keep repository abstractions compatible with future PostgreSQL. Do not add Redis/Kafka without evidence that they are needed.

## Phase 6 — routines and triggers

Support manual, API-event and scheduled triggers first. Design future adapters for GitHub, Slack, email, webhook, filesystem and MCP events.

Require idempotency keys, deduplication, replay protection, failure history, next-run metadata, enable/disable state and tenant scoping. Do not claim integrations that are not actually implemented.

## Phase 7 — policy and approvals

Use explicit decisions: ALLOW, DENY, REQUIRE_APPROVAL.

Capabilities may include:
- workspace.read / workspace.write
- network.http
- model.invoke
- rag.search / rag.ingest
- agent.delegate
- tool.invoke
- connector.read / connector.write
- git.read / git.write
- deployment.execute

Default deny unless explicitly granted. High-impact external writes, publishing, deployment, destructive filesystem/database operations and security/credential changes require approval. The LLM is never the only security boundary.

## Phase 8 — workspace hardening

Preserve per-conversation confinement and test traversal, absolute paths, Unicode tricks, symlink escapes, nested symlinks, races, oversized files, binary confusion, reserved paths and malicious filenames. Never allow cross-tenant or cross-conversation workspace reads.

If process execution is introduced, default it OFF and run it in a dedicated sandbox, never directly against the host.

## Phase 9 — tool/MCP gateway

Create explicit tool manifest/request/result/error/policy abstractions. Tool calls carry tenant, principal, conversation, task, capability and correlation ID. Audit every invocation and grant least privilege.

Future adapters may include MCP, GitHub, filesystem, HTTP, search, database, email, browser and code execution.

## Phase 10 — secrets

Never place provider secrets in browser state, prompts, task envelopes, logs, audit payloads or artifacts. Use secret references and runtime injection after policy evaluation. Redact Authorization headers, cookies, API keys, passwords, tokens and sensitive query parameters. Add regression tests.

## Phase 11 — model router

Preserve local, Kilo, OpenCode and OpenRouter behavior. Keep streaming/fallback contracts. Model/provider metadata should describe local/remote, context limits, availability, health, latency and retryability.

Do not silently send private RAG/context data to remote models. Enforce a data-egress policy in code; sensitive/private document context should remain local by default.

## Phase 12 — RAG security

Add authorization-aware metadata such as tenant, owner, source, classification, creation time, content hash and ingestion status. Apply authorization before retrieval. Treat retrieved text as untrusted data, never privileged instructions. Record provenance.

## Phase 13 — sensitive database boundary

The repository description mentions police-database integration. Never fake, scrape or claim access to a police/government system. Implement only an authorization-aware adapter boundary unless a real approved interface exists. Keep it disabled by default and require authenticated API access, least privilege, role/tenant restrictions, purpose/case reference, PII minimization, audit events and configurable retention.

## Phase 14 — memory

Separate chat history, workflow state, agent memory, RAG documents and audit events. Long-term memory is opt-in/configurable, tenant-scoped, inspectable, deletable and auditable.

## Phase 15 — frontend agentic workspace

Extend the existing React/Vite UI with real backend state for:
- conversation/model/RAG controls
- task queues and statuses
- agent activity/delegation graph
- workspace/files/artifacts
- timeline
- approvals
- provider health/privacy indicators
- audit search

Preserve keyboard access, semantic labels, focus handling, reduced-motion support, responsive layout and safe token handling. Provider secrets stay server-side.

## Phase 16 — audit ledger

Structured audit events include event/time, tenant, principal, conversation, task, event type, action, resource, result and correlation ID. Never log secrets. Important operations must be reconstructable.

## Phase 17 — observability

Use structured logs with request/correlation/task/workflow/agent IDs, provider, duration and outcome. Expose liveness/readiness. Instrument before adding a large observability stack.

## Phase 18 — prompt-injection defense

Keep privileged instructions separate from user messages, RAG documents, tool results, web content and connectors. Add adversarial tests for retrieved text or tool results attempting instruction override, secret disclosure or capability escalation. Security remains enforced by code/policy.

## Phase 19 — network safety

If arbitrary HTTP tools are added, block loopback, link-local, RFC1918 and cloud metadata by default; defend against DNS/redirect-to-private-network attacks; allowlist protocols; enforce timeouts and response-size limits.

## Phase 20 — resilience

Handle duplicate triggers, duplicate tasks, restart, provider timeout, stream interruption, cancellation, approval timeout and child-agent failure. Prefer idempotent operations and persist state before irreversible actions.

## Phase 21 — API

Preserve `/api/v1`. Add typed endpoints only as implemented, e.g. `/agents`, `/tasks`, `/workflows`, `/triggers`, `/approvals`, `/audit`, `/tools`. Return stable safe errors, not internal exceptions.

## Phase 22 — security hardening

Preserve current non-root/read-only containers, dropped capabilities, no-new-privileges, host/CORS validation, production-doc disabling and immutable model verification. Review CSRF, token storage, timing leaks, unsafe deserialization, subprocesses, SSRF, XSS/CSP, temp files, TOCTOU, symlinks, archive traversal, prompt injection and tenant isolation. Never weaken a safeguard just to make CI green.

## Phase 23 — container security

Maintain read-only roots, non-root users, `no-new-privileges`, `cap_drop: ALL`, loopback defaults, explicit writable paths, no Docker socket and no privileged mode.

## Phase 24 — CI/CD

Keep CI blocking. Required categories remain backend lint/type/test/security, frontend lint/test/build/audit, Compose validation, Docker build, conditional ShellCheck, CodeQL and dependency review. Never hide meaningful failures with `|| true`, `|| echo` or unjustified `continue-on-error`.

## Phase 25 — tests

Add tests for:
- authentication and verified identity
- cross-tenant isolation
- workspace traversal/symlink/size limits
- delegation/depth/cycles/cancellation
- workflow success/failure/retry/approval/resume/idempotency
- policy allow/deny/approval/escalation
- secret redaction
- provider failover/local fallback/SSE/data-egress restrictions
- RAG authorization and malicious injection content

## Phase 26 — documentation

Keep README, QUICKSTART, SECURITY, CONTRIBUTING and CHANGELOG synchronized with actual behavior. Add focused architecture/security/workflow/deployment/migration docs only when useful. Never document aspirational features as implemented.

## Phase 27 — agent development instructions

Use one canonical repository-level instruction source. Tool-specific copies should point to or be generated from it when possible. Since PR #8 may own `.codex`, `.claude` and `.agents`, reconcile rather than overwrite.

## Phase 28 — local-first / zero-cost

Keep local GGUF, SQLite, filesystem artifacts, Docker Compose and open-source tooling as first-class defaults. Remote providers remain optional. Do not make a paid SaaS mandatory.

## Phase 29 — performance

Preserve lazy expensive initialization. Measure model startup, embedding startup, RAG latency, DB locking, SSE behavior, frontend bundle size and workflow overhead before optimizing. Avoid busy polling.

## Phase 30 — migrations

Any persistent schema change requires a version, migration, backup guidance, rollback plan and tests. Never silently treat incompatible historical data as empty.

## Required engineering loop

INSPECT → DESIGN → IMPLEMENT → TEST → SECURITY REVIEW → FIX → RETEST → DOCUMENT

Prefer small coherent commits, not a giant untested patch.

## Required validation

Run the repository's real gates:

```bash
make lint
make test
make security
make shellcheck
make docker-build
docker compose config --quiet
```

Run frontend checks explicitly if Make does not cover them. Never report a pass unless it ran and passed. Report environment limitations precisely.

## Git rules

Start with status/fetch/current branch/log. Never discard unrelated work, force push or commit secrets. Use focused conventional commits.

## Definition of done

Do not call the program complete until existing functionality remains operational, new APIs are tested, tenant/workspace/RAG boundaries are proven, policy is enforced in code, delegation is bounded, workflow state persists, approvals work, remote egress is controlled, secrets stay server-side, frontend reflects real state, quality/security/build gates pass and docs match reality.

## Evidence vocabulary

Use only: IMPLEMENTED, TESTED, VERIFIED, PARTIAL, NOT IMPLEMENTED, BLOCKED.

Separate implementation evidence from deployment evidence. A Docker build is not production deployment, a backup script is not restore proof, replicas in YAML are not HA proof, and region configuration is not multi-region proof.

## Final report

Return:
1. executive summary
2. architecture before/after
3. files changed by subsystem
4. API compatibility
5. security changes and findings
6. exact tests/commands/results
7. CI/CD status
8. migration/rollback
9. evidence matrix
10. remaining gaps
11. branch, commits, PR and final SHA

Start by re-reading the latest `main`, open PRs, Actions state, repository tree, current security boundaries and Cowork implementation. Then execute all feasible work end-to-end.
