# AI-DBC Production Evidence & Release Gate Prompt

Act as release manager and independent verifier for `cvsz/ai-dbc`. Determine exactly what is ready to merge/release and what is not. Do not add speculative features.

Re-read latest `main` and all open PRs before validation, including any PR that owns `.codex`, `.claude` or `.agents` files.

## Review

Compare the implementation branch with `main` and inspect every diff, migration, config change, API compatibility boundary, frontend/backend contract and security-relevant behavior.

## Required commands

Where supported by the repository, run:

```bash
git status
git diff --check
make lint
make test
make security
make shellcheck
docker compose config --quiet
make docker-build
```

Start the stack when feasible and verify:
- frontend
- backend health
- model catalog
- conversation creation
- workspace creation/read/write
- agent registry
- task creation
- workflow execution
- approval flow
- audit events
- RAG
- local-model route
- remote-provider policy
- SSE streaming

Do not download a huge model merely to manufacture a smoke-test pass. Distinguish “API behavior tested” from “model inference tested”.

## Rollback/migration

Verify new agentic functionality can be disabled or rolled back without breaking intended historical chat/RAG behavior. Check migration paths for existing SQLite/RAG/workspace data.

Update docs only to match proven behavior.

## Release matrix

Use only YES, NO, PARTIAL, N/A.

| Capability | Implemented | Automated test | Runtime verified | Production evidenced |
|---|---|---|---|---|
| Local chat | | | | |
| Remote routing | | | | |
| RAG | | | | |
| Cowork workspace | | | | |
| Agent registry | | | | |
| Multi-agent delegation | | | | |
| Workflow engine | | | | |
| Triggers | | | | |
| Approval engine | | | | |
| Policy engine | | | | |
| Tenant isolation | | | | |
| Audit trail | | | | |
| MCP/tool gateway | | | | |
| Secret broker | | | | |
| Docker deployment | | | | |

Then report:

```text
DEPLOY READY:
PRODUCTION EVIDENCED:
REAL DR VERIFIED:
HA VERIFIED:
MULTI-REGION VERIFIED:
BACKUP RESTORE VERIFIED:
SECURITY REVIEW PASSED:
TENANT ISOLATION VERIFIED:
```

A local Docker build does not prove production deployment. A backup script does not prove restore. Replicas in YAML do not prove HA. A region field does not prove multi-region.

Finally provide branch, base SHA, final SHA, commits, PR, CI status, blockers, rollback instructions and exact next actions.

Return `MERGE CANDIDATE: YES` only when required merge gates pass; otherwise return `MERGE CANDIDATE: NO` with precise blockers. Never manufacture evidence.
