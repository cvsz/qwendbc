# Production-Readiness Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing AI-DBC repository reproducible, secure, and internally consistent without changing its public API or adding product capabilities.

**Architecture:** Keep FastAPI services and routes intact, use `frontend/src/api.js` as the sole browser API boundary, and add focused regression coverage around the existing contracts. Keep deployment and CI changes declarative and conservative, preserving loopback defaults and server-side provider credentials.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, pytest, Black, Flake8, mypy, React 19, Vite, Node test runner, Docker Compose, Nginx, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-12-production-readiness-design.md`

## Global Constraints

- Do not change the public API or add new product capabilities.
- Preserve unrelated uncommitted work already present in the worktree.
- Protected endpoints continue to require the configured bearer token.
- Provider credentials remain server-side and model/RAG operations stay off the ASGI event loop.
- Streaming releases remote capacity on success, failure, and disconnect.
- Do not commit environments, secrets, model files, caches, or generated build output.
- Environment/tool failures must be reported separately from code failures.

## File Map

- `frontend/src/api.js`: shared authenticated browser request functions.
- `frontend/src/ControlPanel.jsx`: model/runtime controls and their UI state.
- `frontend/src/ControlPanel.css`: control-panel presentation only if UI removal requires cleanup.
- `frontend/src/App.jsx`: chat-level state and any existing route controls.
- `frontend/src/api.test.js`: request/auth regression tests.
- `backend/tests/test_main.py`: HTTP route and lifecycle regression tests.
- `backend/tests/test_model_router.py`: provider/model validation regressions.
- `backend/tests/test_production_hardening.py`: security/configuration regressions.
- `Makefile`, `backend/requirements*.txt`, `frontend/package*.json`, Docker and workflow files: reproducibility and quality-gate consistency.
- Documentation under `README.md`, `QUICKSTART.md`, `docs/`, and `CHANGELOG.md`: final behavior and setup instructions.

### Task 1: Establish a clean baseline and protect the worktree

**Files:**
- Read-only: `git status`, `git diff`, repository manifests and test configuration.

**Interfaces:**
- Produces a list of pre-existing changes and available local tools for every later task.

- [ ] **Step 1: Record the current worktree state**

Run:

```bash
git status --short
git diff --stat
git diff --check
```

Expected: existing changes are documented mentally; no reset, checkout, clean, or broad deletion is performed.

- [ ] **Step 2: Run available baseline checks independently**

Run:

```bash
cd frontend && npm test
cd ..
if [ -x .venv/bin/pytest ]; then PYTHONPATH=backend .venv/bin/pytest -c backend/pyproject.toml backend/tests; fi
```

Expected: frontend results are classified as code pass/fail; a broken `.venv` is classified as an environment failure.

### Task 2: Centralize authenticated control-panel API access

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/ControlPanel.jsx`
- Test: `frontend/src/api.test.js`

**Interfaces:**
- Consumes: `apiRequest(path, options)`, `getAccessToken()`, and the existing `/api/v1` base URL.
- Produces: exported `fetchModelInfo(options)`, `unloadModel(options)`, and shared `fetchHealth(options)` behavior used by the control panel.

- [ ] **Step 1: Add failing helper/auth tests**

Add tests that call the model-info and unload helpers with a fake `sessionStorage` containing `ai-dbc.accessToken`, then assert the request includes `Authorization: Bearer test-token`, the expected URL, and the expected method.

- [ ] **Step 2: Run the focused frontend test**

Run:

```bash
cd frontend && npm test
```

Expected: the new helper tests fail because the helpers are not exported or the control panel still bypasses them.

- [ ] **Step 3: Implement the shared helpers and migrate the panel**

Export:

```js
export function fetchModelInfo(options = {}) {
  return apiRequest("/model/info", { method: "GET", ...options });
}

export function unloadModel(options = {}) {
  return apiRequest("/model/unload", { method: "POST", ...options });
}
```

Update `ControlPanel.jsx` to import the shared helpers, use them for health/model-info/load/unload, and remove its private `requestJson`/error parser. Preserve existing user-visible error states.

- [ ] **Step 4: Run focused tests and lint**

Run:

```bash
cd frontend && npm test && npm run lint
```

Expected: PASS.

### Task 3: Remove the unsupported streaming-toggle behavior

**Files:**
- Modify: `frontend/src/ControlPanel.jsx`
- Modify: `frontend/src/ControlPanel.css` only for now-unused selectors
- Test: `frontend/src/api.test.js` if a request helper is affected

**Interfaces:**
- Consumes: existing request-level `stream` support in the backend contract.
- Produces: a control panel that does not issue requests to nonexistent `/model/streaming`.

- [ ] **Step 1: Add a static regression check**

Add a Node test that reads `ControlPanel.jsx` as text and asserts it contains no `"/model/streaming"` reference and no private `requestJson` function.

- [ ] **Step 2: Run the focused test and observe failure**

Run:

```bash
cd frontend && npm test
```

Expected: the new check fails against the current control panel.

- [ ] **Step 3: Remove the toggle and stale state**

Delete the `streaming` state, `toggleStreaming`, and Generation toggle section. Do not add a new global setting; request-level streaming remains available to API clients without changing the product UI.

- [ ] **Step 4: Run frontend verification**

Run:

```bash
cd frontend && npm test && npm run lint && npm run build
```

Expected: PASS with no unused CSS or JSX references.

### Task 4: Add backend lifecycle and streaming regression coverage

**Files:**
- Modify: `backend/tests/test_main.py`
- Modify: `backend/tests/test_production_hardening.py`
- Modify: `backend/tests/test_model_router.py` only where existing fixtures need exact contract assertions

**Interfaces:**
- Consumes: existing FastAPI dependency overrides, `ChatRequest`, `ModelRouter`, and fake services.
- Produces: tests proving protected model-info/unload/catalog routes, request-level `stream: true`, and lease cleanup behavior.

- [ ] **Step 1: Write failing tests for protected lifecycle access**

With a test `Settings` containing `QWENDBC_ACCESS_TOKEN="test-token"`, call `/api/v1/model/info` and `/api/v1/model/unload` without a token and assert 401; repeat with `Authorization: Bearer test-token` and assert the fake service is reached.

- [ ] **Step 2: Write failing request-level streaming test**

Post to `/api/v1/chat/completions` with `{"messages":[{"role":"user","content":"hello"}],"stream":true}` and a fake router stream yielding one valid chunk. Assert `text/event-stream`, the chunk, and `data: [DONE]`.

- [ ] **Step 3: Write failing cleanup test**

Use a fake stream that raises after yielding or is closed early, then assert the test lease’s `release()` is called exactly once.

- [ ] **Step 4: Run focused backend tests**

Run:

```bash
PYTHONPATH=backend python -m pytest -c backend/pyproject.toml backend/tests/test_main.py backend/tests/test_production_hardening.py backend/tests/test_model_router.py -q
```

Expected: tests fail only where the current implementation violates the specified contract; fixture/environment errors are recorded separately.

- [ ] **Step 5: Make the smallest backend correction required by failing tests**

Preserve existing endpoint paths and response schemas. If the tests expose only fixture assumptions, correct the fixtures instead of production code. Keep all blocking model/provider calls in `asyncio.to_thread()` or the existing synchronous iterator boundary.

- [ ] **Step 6: Re-run focused tests**

Run the same command and expect PASS.

### Task 5: Repair reproducibility and dependency/configuration consistency

**Files:**
- Modify: `Makefile`
- Modify: `backend/requirements.txt`
- Modify: `backend/requirements-dev.txt`
- Modify: `frontend/package.json`, `frontend/package-lock.json` only when dependency metadata is inconsistent
- Modify: `.gitignore`, `.env.example`, `configs/.env.example`, Dockerfiles, or Compose files only when validation identifies a concrete mismatch

**Interfaces:**
- Consumes: current Python 3.13/Node 24 declarations and lockfiles.
- Produces: setup that creates or uses only repository-local environments and manifests that install reproducibly.

- [ ] **Step 1: Verify setup path assumptions**

Run:

```bash
rg -n "qwendbc|ai-dbc|\.venv|node_modules|package-lock|requirements" Makefile README.md QUICKSTART.md backend frontend docker-compose*.yml docker
```

Expected: no setup command relies on an external absolute interpreter path.

- [ ] **Step 2: Validate manifest and lockfile consistency**

Run:

```bash
cd frontend && npm ci --ignore-scripts --no-audit --no-fund
```

Expected: install succeeds or the failure identifies a concrete lockfile/dependency issue to fix.

- [ ] **Step 3: Upgrade only compatible dependencies**

Use the repository’s declared compatibility ranges and lockfile resolution. Do not perform an unbounded “latest everything” upgrade. For each changed dependency, run the relevant tests/build/audit and document breaking changes in `CHANGELOG.md`.

- [ ] **Step 4: Verify setup and manifests**

Run:

```bash
make -n setup
cd frontend && npm ci --ignore-scripts --no-audit --no-fund && npm test && npm run build
```

Expected: commands reference local project paths and the lockfile remains valid.

### Task 6: Validate CI, deployment files, and documentation

**Files:**
- Modify: `.github/workflows/*.yml`, `.github/dependabot.yml`, and `.github/*.yml` only for concrete schema/reference issues
- Modify: `docker-compose.yml`, `docker-compose.prod.yml`, `docker-compose.acme.yml`, `docker/*.conf`, and `deploy/*` only for concrete Compose/deployment issues
- Modify: `README.md`, `QUICKSTART.md`, `docs/api/README.md`, `docs/deployment/docker.md`, `docs/security/overview.md`, `docs/user-guide/*.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: the final backend/frontend behavior from Tasks 2–5.
- Produces: documentation and automation that describe and validate the same commands, endpoints, ports, auth behavior, and files.

- [ ] **Step 1: Check all referenced repository files and commands**

Run:

```bash
rg -n "codeql\.yml|dependency-review\.yml|stale\.yml|labeler\.yml|docker-compose|model/streaming|QwenDBC|AI-DBC|qwendbc" README.md QUICKSTART.md docs .github docker Makefile frontend backend
```

Expected: stale branding, nonexistent endpoints, and inaccurate commands are identified.

- [ ] **Step 2: Validate workflow YAML and Compose configuration**

Run, when tools are available:

```bash
docker compose config --quiet
docker compose -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.acme.yml config --quiet
```

Expected: all configs parse successfully; unavailable Docker is reported as an environment limitation.

- [ ] **Step 3: Update only inaccurate documentation/configuration**

Ensure protected control-panel actions, request-level streaming, local-first defaults, upload limits, production token/revision requirements, and Docker paths match the final code. Keep provider keys out of browser examples.

- [ ] **Step 4: Run a final reference scan**

Run:

```bash
rg -n "TODO|FIXME|/model/streaming|QwenDBC|qwendbc|placeholder|not implemented" --glob '!docs/superpowers/**' .
```

Expected: no stale runtime references remain; historical changelog mentions are acceptable only when clearly historical.

### Task 7: Execute the full verification gate and hand off

**Files:**
- Read-only verification of all changed files.

**Interfaces:**
- Consumes: all implementation and documentation changes.
- Produces: verified repository state and a concise report separating passed checks, code failures, and unavailable tools.

- [ ] **Step 1: Run backend quality gates**

```bash
make lint-backend
make test-backend
```

- [ ] **Step 2: Run frontend quality gates**

```bash
make test-frontend
make lint-frontend
```

- [ ] **Step 3: Run security and deployment gates when available**

```bash
make security
make shellcheck
make docker-build
```

- [ ] **Step 4: Review the final diff without altering unrelated work**

```bash
git diff --check
git diff --stat
git status --short
```

Expected: no whitespace errors, no generated artifacts/secrets, and all pre-existing user changes remain present.

- [ ] **Step 5: Report completion accurately**

Report changed files, tests that passed, tools unavailable or blocked by environment, and any dependency upgrades that were intentionally not applied because compatibility could not be verified.
