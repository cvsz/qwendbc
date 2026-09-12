# AI-DBC Adversarial Security & Architecture Review Prompt

Act as the independent principal security architect for `cvsz/ai-dbc`. Review the implementation branch against the latest `main`. Do not begin by adding features. Try to disprove the safety and production-readiness claims.

## Required focus

Review authentication, authorization, tenant isolation, capability escalation, agent delegation, approval bypass, workflow integrity, workspace traversal/symlink escape, arbitrary file access, command execution, subprocess handling, SSRF, secret/log/frontend leakage, prompt injection, RAG poisoning, remote-model data exfiltration, tool-output injection, connector/MCP privilege inheritance, DoS, recursion, replay/duplicate triggers, races, cancellation, audit gaps, crypto/randomness, dependencies, Docker privileges, exposed ports and CI bypasses.

Test these trust boundaries:

```text
User -> API
Tenant A -> Tenant B
Conversation A -> Conversation B
Agent -> Agent
Agent -> Tool
Agent -> Workspace
Agent -> Remote Model
RAG -> Agent
Tool Result -> Agent
Trigger -> Workflow
Workflow -> Approval
Approval -> Executor
Container -> Host
```

Verify that security is enforced by application/runtime code, not only prompt instructions.

## Required adversarial cases

1. `../` workspace traversal
2. absolute-path access
3. symlink escape
4. another tenant's conversation ID
5. another tenant's task ID
6. another tenant's RAG document
7. forged role/scope values
8. approval replay
9. child-agent capability escalation
10. delegation cycle
11. excessive recursion
12. duplicate webhook/trigger
13. malicious RAG text saying to ignore prior instructions
14. tool output requesting secret disclosure
15. private context routed remotely while egress is denied
16. Authorization header in logs
17. API key in errors
18. loopback/private-network SSRF
19. redirect to metadata/private network
20. workflow resume after crash

## Docker checks

Require non-root execution, read-only root filesystem, no-new-privileges, cap-drop ALL, no Docker socket, no privileged mode, minimum explicit writable mounts and loopback exposure defaults.

## CI checks

Reject important security/quality commands hidden behind `|| true`, `|| echo` or unjustified `continue-on-error`.

Run at minimum:

```bash
make lint
make test
make security
make shellcheck
make docker-build
docker compose config --quiet
```

Do not weaken tests to make them pass.

## Reporting

Order findings CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL.

For every finding include:
- ID
- severity
- affected file/component
- attack path
- impact
- concrete evidence
- recommended fix
- verification test

After remediation, rerun relevant checks.

Finish with:

```text
Authentication             PASS / FAIL / PARTIAL
Tenant isolation           PASS / FAIL / PARTIAL
Workspace isolation        PASS / FAIL / PARTIAL
Agent capability model     PASS / FAIL / PARTIAL
Approval enforcement       PASS / FAIL / PARTIAL
Secret isolation           PASS / FAIL / PARTIAL
RAG isolation              PASS / FAIL / PARTIAL
Remote egress control      PASS / FAIL / PARTIAL
SSRF protection            PASS / FAIL / PARTIAL
Container hardening        PASS / FAIL / PARTIAL
CI security gates          PASS / FAIL / PARTIAL
Auditability               PASS / FAIL / PARTIAL
```

Do not use “production ready” unless critical boundaries have concrete test evidence.
