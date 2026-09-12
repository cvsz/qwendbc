# AionUi Integration Plan

This branch ports the **architecture and product capabilities** of iOfficeAI/AionUi into AI-DBC rather than replacing AI-DBC with an upstream repository snapshot.

## Upstream

- Project: https://github.com/iOfficeAI/AionUi
- Upstream license: Apache-2.0
- Upstream revision reviewed for this plan: `6744099b279b991c17e31c243f0920477bd31cb6`

Any directly reused upstream source must retain its Apache-2.0 copyright/license notices and must not be relabeled as MIT-only code. New AI-DBC code remains under the repository's existing license.

## Target architecture

AI-DBC keeps its existing local-first FastAPI + React + SQLite/RAG foundation and adds an AionUi-inspired Cowork layer:

1. **Agent runtime**
   - Built-in agent execution loop.
   - Tool invocation with explicit approval boundaries.
   - Multi-step task state and resumability.
   - Local workspace/file operations.

2. **Multi-agent adapter layer**
   - Provider-neutral agent interface.
   - ACP/CLI adapter boundary for supported external coding agents.
   - Manual model/agent selection; no implicit provider fallback unless explicitly enabled.

3. **Conversation/workspace layer**
   - Persistent conversations.
   - Per-conversation working directory.
   - Attachments and file references.
   - Timeline/event model suitable for streaming agent activity.

4. **Model/provider layer**
   - Preserve AI-DBC's normalized provider catalog.
   - Provider credentials remain server-side.
   - Support multiple model providers through adapters.
   - Keep local inference as a first-class backend.

5. **Automation layer**
   - Scheduled jobs.
   - Agent task queue.
   - Durable execution state.
   - Explicit security policy for unattended tasks.

6. **WebUI/remote access**
   - Reuse AI-DBC's authenticated API boundary.
   - WebSocket/SSE event streaming.
   - No public backend exposure by default.

## Initial modules to implement

```text
backend/
  agents/
    core.py
    registry.py
    execution.py
    approvals.py
  adapters/
    base.py
    builtin.py
    acp.py
  workspace/
    manager.py
    files.py
  conversations/
    service.py
    timeline.py
  automation/
    scheduler.py
    jobs.py
  events/
    bus.py

frontend/
  src/
    agents/
    conversations/
    workspace/
    components/
    services/
```

## Security requirements

- Never expose provider API keys to the browser.
- Keep backend binding loopback/private by default.
- Require the existing AI-DBC bearer token for protected remote operations.
- Treat filesystem, shell, network, and process tools as privileged capabilities.
- Record approval decisions and agent tool events.
- Apply workspace path confinement and reject traversal outside the configured workspace.
- Keep remote-provider routing opt-in.

## Acceptance criteria

- Existing `/api/v1/chat/completions` behavior remains compatible.
- Local RAG continues to work without enabling remote providers.
- An agent can create a workspace, inspect files, modify files, and report a structured timeline.
- Agent execution can stream progress to the React UI.
- Tool execution requires policy/approval according to configuration.
- Existing lint, tests, security checks, Docker build, and frontend build remain blocking CI gates.

## Important licensing note

AionUi is Apache-2.0. If individual upstream source files are copied verbatim or materially incorporated, preserve the applicable copyright and license notices and retain a record of the upstream revision. Prefer implementing equivalent interfaces and behavior in AI-DBC-specific code when direct source reuse is unnecessary.
