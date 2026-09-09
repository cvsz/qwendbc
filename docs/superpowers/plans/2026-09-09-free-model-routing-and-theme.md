# Free-Model Routing and Premium Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe free-model routing across Kilo, OpenCode, OpenRouter, and local Qwen, then expose it through a premium responsive day/night/system React experience and verify the public deployment.

**Architecture:** Keep `LLMService` as the local provider and place all hosted providers behind one OpenAI-compatible adapter. `ModelRouter` owns catalog normalization, free/text filtering, explicit selection, and per-request fallback; FastAPI dependencies enforce the optional application bearer token and bounded limits. The React app consumes the normalized model catalog, keeps chat behavior backward compatible, and applies a tokenized responsive theme system.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, `httpx`, llama-cpp-python, pytest, React 19, Vite, oxlint, CSS custom properties, Docker Compose, Nginx.

## Global Constraints

- Never commit, print, or copy API keys from any `.env.ai` file.
- Automatic routing may select only free text-chat models; OpenRouter `openrouter/auto`, OpenCode Go, and Kilo paid/credit routes are excluded.
- `REMOTE_MODELS_ENABLED=false` remains the safe default; enabling public hosted chat requires `QWENDBC_ACCESS_TOKEN`.
- Preserve local GGUF model lifecycle, document upload/search, RAG service, existing API routes, Docker loopback defaults, and CI gates.
- Do not download or load the GGUF model during an arbitrary remote request.
- Follow test-first development: each behavioral change begins with a failing test and a focused red/green/refactor cycle.
- Use mobile-first CSS, 44px minimum interactive targets, relative units, WCAG AA contrast, and `prefers-reduced-motion` support.
- Use direct imports, lazy/deferred work where useful, stable effect dependencies, and avoid unnecessary React re-renders.
- Keep provider credentials, filesystem paths, raw upstream responses, and internal exception details out of public responses.

---

## Repository map and boundaries

### Backend routing subsystem

- Create `backend/app/services/provider_types.py` for provider model metadata,
  normalized completion types, provider protocols, and safe provider errors.
- Create `backend/app/services/remote_provider.py` for one reusable synchronous
  OpenAI-compatible adapter covering Kilo, OpenCode, and OpenRouter.
- Create `backend/app/services/model_router.py` for local/remote provider
  registration, free catalog filtering, cache, explicit selection, fallback,
  and stream boundary behavior.
- Create `backend/app/services/access_control.py` for bearer-token validation,
  fixed-window request limiting, and bounded remote concurrency.
- Modify `backend/app/schemas/config.py` with validated provider URLs, model
  mode, provider order, access token, timeout, rate, and concurrency settings.
- Modify `backend/app/schemas/chat.py` with request provider/model/RAG fields,
  normalized catalog responses, and non-secret completion metadata.
- Modify `backend/app/routers/chat.py` to use the router and protection
  dependencies while retaining existing paths and local lifecycle endpoints.
- Modify `backend/app/routers/documents.py` to protect document mutation and
  search when application authentication is configured.
- Modify `backend/app/main.py` only as needed to expose the shared router and
  keep shutdown behavior deterministic.
- Modify `backend/requirements.txt` to add the pinned-compatible `httpx` range.
- Add `backend/tests/test_provider_types.py`,
  `backend/tests/test_remote_provider.py`,
  `backend/tests/test_model_router.py`, and
  `backend/tests/test_access_control.py`; extend existing API tests without
  weakening their local compatibility assertions.

### Frontend experience subsystem

- Create `frontend/src/theme.js` with pure theme preference resolution and
  persistence helpers so it can be tested without a browser renderer.
- Create `frontend/src/api.js` with API URL/auth-aware request helpers,
  response parsing, catalog fetching, and SSE parsing.
- Replace `frontend/src/App.jsx` with composed header, theme control, provider
  selector, catalog/status panel, chat transcript, and composer behavior.
- Replace `frontend/src/App.css` with mobile-first design tokens, day/night
  palettes, responsive layout, focus states, reduced-motion rules, and
  premium surfaces.
- Modify `frontend/src/main.jsx` only if a pre-paint theme initialization hook
  is needed to prevent a light/dark flash.
- Modify `frontend/package.json` only for the smallest test dependency needed
  to exercise `theme.js`; keep the existing Vite/oxlint build path intact.
- Add `frontend/src/theme.test.js` and `frontend/src/api.test.js` if the
  chosen test runner can run them without a full browser; otherwise keep pure
  helper tests in the backend-compatible release check and use Playwright for
  the rendered smoke test.

### Documentation and release subsystem

- Modify `configs/.env.example` with safe provider and security settings.
- Modify `docker-compose.yml` only if explicit environment forwarding or a
  health/readiness check is required; preserve loopback publishing defaults.
- Modify `README.md` and `QUICKSTART.md` with free-provider configuration,
  bearer-token behavior, catalog/chat examples, theme behavior, and rollback.
- Add/modify CI only when the frontend test command or dependency lockfile
  requires it; do not hide new failures behind `|| true`.
- Do not modify Terraform/Cloudflare route ownership until local implementation
  and authenticated public verification prove that the existing route needs it.

## Task 1: Add validated configuration and provider data contracts

**Files:**
- Modify: `backend/app/schemas/config.py`
- Modify: `backend/app/schemas/chat.py`
- Create: `backend/app/services/provider_types.py`
- Modify: `backend/requirements.txt`
- Modify: `configs/.env.example`
- Test: `backend/tests/test_provider_types.py`
- Test: `backend/tests/test_main.py`

**Interfaces:**
- `Settings.MODEL_MODE: Literal["local", "auto_free"]` defaults to
  `"auto_free"`.
- `Settings.FREE_PROVIDER_ORDER: str` defaults to
  `"kilo,opencode,openrouter,local"` and exposes a parsed tuple property.
- `Settings.REMOTE_MODELS_ENABLED: bool` defaults to `False`.
- `Settings.QWENDBC_ACCESS_TOKEN: str` defaults to an empty string and is
  handled as secret data: never include it in `repr`, logs, or responses.
- `Settings.REMOTE_REQUEST_TIMEOUT_SECONDS`,
  `Settings.REMOTE_MAX_CONCURRENT_REQUESTS`, and
  `Settings.REMOTE_RATE_LIMIT_PER_MINUTE` have positive bounded fields.
- Provider URL/model/key fields use the names from the approved spec.
- `ProviderModel` is a frozen dataclass with `provider`, `id`, `name`, `free`,
  `supports_chat`, and optional `context_length`/pricing fields.
- `ProviderError` carries a safe public message and `retryable: bool`.

- [ ] **Step 1: Write the failing settings and metadata tests.**

```python
def test_default_free_order_is_provider_safe() -> None:
    config = Settings(_env_file=None)
    assert config.MODEL_MODE == "auto_free"
    assert config.free_provider_order == ("kilo", "opencode", "openrouter", "local")
    assert config.REMOTE_MODELS_ENABLED is False


def test_remote_mode_requires_access_token() -> None:
    with pytest.raises(ValueError, match="QWENDBC_ACCESS_TOKEN"):
        Settings(_env_file=None, REMOTE_MODELS_ENABLED=True)


def test_provider_model_does_not_expose_secret_fields() -> None:
    model = ProviderModel(provider="kilo", id="kilo-auto/free", name="Auto Free", free=True)
    assert "api_key" not in repr(model).lower()
```

- [ ] **Step 2: Run the focused tests and verify the expected red failure.**

```bash
PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_provider_types.py backend/tests/test_main.py -k 'free_order or remote_mode or provider_model'
```

Expected: FAIL because the new settings fields and provider contract do not
exist yet.

- [ ] **Step 3: Implement the smallest configuration and contract changes.**

Add typed fields and a cross-field validator that rejects
`REMOTE_MODELS_ENABLED=True` without a nonblank token, rejects unknown/duplicate
provider-order entries, and preserves all existing model/RAG validators. Add
the provider dataclass and safe error type. Add `httpx>=0.28,<1.0` to runtime
requirements and add empty/non-secret examples to `configs/.env.example`.

- [ ] **Step 4: Re-run the focused tests and existing settings tests.**

Run the command from Step 2, then:

```bash
PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_main.py
```

Expected: PASS with all existing API/settings tests preserved.

- [ ] **Step 5: Commit the configuration boundary.**

```bash
git add backend/app/schemas/config.py backend/app/schemas/chat.py \
  backend/app/services/provider_types.py backend/requirements.txt \
  configs/.env.example backend/tests/test_provider_types.py backend/tests/test_main.py
git commit -m "feat: add free model provider configuration"
```

## Task 2: Implement remote provider catalog and completion adapters

**Files:**
- Create: `backend/app/services/remote_provider.py`
- Test: `backend/tests/test_remote_provider.py`

**Interfaces:**
- `OpenAICompatibleProvider(name, base_url, api_key, default_model, free_ids, timeout_seconds)`.
- `OpenAICompatibleProvider.is_configured() -> bool`.
- `OpenAICompatibleProvider.list_models(refresh: bool = False) -> list[ProviderModel]`.
- `OpenAICompatibleProvider.complete(messages, model, temperature, top_p, max_tokens) -> dict[str, Any]`.
- `OpenAICompatibleProvider.stream(messages, model, temperature, top_p, max_tokens) -> Iterator[dict[str, Any]]`.
- `OpenAICompatibleProvider.free_model_ids` must include route aliases only
  for the provider that owns them; OpenCode `auto` resolves from its allowlist.

- [ ] **Step 1: Write failing catalog, payload, error, and SSE tests.**

```python
def test_kilo_catalog_keeps_only_free_text_models(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    monkeypatch.setattr(provider, "_get_json", lambda _: {"data": [
        {"id": "stepfun/step-3.7-flash:free", "name": "Step", "pricing": {"prompt": "0", "completion": "0"}, "architecture": {"output_modalities": ["text"]}},
        {"id": "paid/model", "name": "Paid", "pricing": {"prompt": "1", "completion": "1"}, "architecture": {"output_modalities": ["text"]}},
        {"id": "google/lyria-3-pro-preview", "name": "Audio", "pricing": {"prompt": "0", "completion": "0"}, "architecture": {"output_modalities": ["audio"]}},
    ]})
    assert [model.id for model in provider.list_models(refresh=True)] == ["stepfun/step-3.7-flash:free"]


def test_complete_sends_openai_compatible_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("openrouter", "https://router.test", default_model="openrouter/free")
    response = {"id": "x", "model": "openrouter/free", "choices": [{"message": {"content": "ok"}}], "usage": {}}
    monkeypatch.setattr(provider, "_post_json", lambda path, payload: response)
    result = provider.complete([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32)
    assert result["choices"][0]["message"]["content"] == "ok"


def test_stream_parses_data_lines_until_done(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    monkeypatch.setattr(provider, "_stream_response", lambda *_: [
        'data: {"choices":[{"delta":{"content":"hi"}}]}',
        "data: [DONE]",
    ])
    chunks = list(provider.stream([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32))
    assert chunks[0]["choices"][0]["delta"]["content"] == "hi"
```

- [ ] **Step 2: Run the adapter tests and verify they fail for missing adapter behavior.**

```bash
PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_remote_provider.py
```

Expected: FAIL because the adapter and helpers do not exist.

- [ ] **Step 3: Implement the adapter with bounded network behavior.**

Use synchronous `httpx.Client` calls because FastAPI already runs these
CPU/network-bound provider calls in worker threads. Normalize `/models` data
from either a top-level `data` array or a raw array. Treat `0`, `"0"`, and
`"0.0"` prices as free only when both prompt and completion prices are zero.
Inspect output modalities and reject non-text-only entries. Use provider
specific free aliases (`kilo-auto/free`, `openrouter/free`) and OpenCode's
explicit allowlist. Send only `messages`, `model`, `temperature`, `top_p`,
`max_tokens`, and `stream` in chat payloads. Convert timeout/request/HTTP
responses into `ProviderError` without including response bodies in its public
message. Parse `data:` SSE lines, ignore comments/blank lines, stop on
`[DONE]`, and preserve valid OpenAI-compatible chunk objects.

- [ ] **Step 4: Re-run adapter tests and add malformed/timeout cases.**

```bash
PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_remote_provider.py
```

Add tests that a malformed catalog returns an empty list, a 429 is retryable,
401 is non-retryable, and a missing `choices` response raises a safe provider
error. Expected: all focused tests pass.

- [ ] **Step 5: Commit the adapter.**

```bash
git add backend/app/services/remote_provider.py backend/tests/test_remote_provider.py
git commit -m "feat: add OpenAI-compatible free provider adapter"
```

## Task 3: Add router fallback, catalog API, authentication, and limits

**Files:**
- Create: `backend/app/services/access_control.py`
- Create: `backend/app/services/model_router.py`
- Modify: `backend/app/schemas/chat.py`
- Modify: `backend/app/routers/chat.py`
- Modify: `backend/app/routers/documents.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_model_router.py`
- Test: `backend/tests/test_access_control.py`
- Modify: `backend/tests/test_main.py`
- Modify: `backend/tests/test_rag.py`

**Interfaces:**
- `ModelRouter(local_service, config=settings)`.
- `ModelRouter.list_models(refresh=False) -> ModelsResponse`.
- `ModelRouter.complete(messages, provider=None, model=None, temperature=..., top_p=..., max_tokens=..., rag_sources=None) -> dict[str, Any]`.
- `ModelRouter.stream(messages, provider=None, model=None, temperature=..., top_p=..., max_tokens=...) -> Iterator[dict[str, Any]]`.
- `ModelRouter.get_model_info() -> dict[str, Any]` retains `name`, `path`,
  `context_length`, `threads`, and `loaded`, and adds only non-secret provider
  status fields.
- `require_access(request: Request) -> None` allows local operation when no
  token is configured and enforces constant-time bearer comparison when one is.
- `guarded_remote_call()` is a context manager that acquires the configured
  bounded semaphore and raises a safe 429 if capacity is exhausted.

- [ ] **Step 1: Write failing router and security tests.**

```python
def test_auto_mode_uses_configured_order_and_skips_rate_limited_provider() -> None:
    providers = [
        FakeProvider("kilo", error=ProviderError("busy", retryable=True)),
        FakeProvider("opencode", text="answer"),
    ]
    router = ModelRouter(FakeLocalService(loaded=False), make_settings(), providers=providers)
    result = router.complete([{"role": "user", "content": "hello"}], max_tokens=16)
    assert result["choices"][0]["message"]["content"] == "answer"
    assert result["qwendbc"]["provider"] == "opencode"
    assert result["qwendbc"]["fallback"] is True


def test_local_provider_is_final_fallback_when_loaded() -> None:
    providers = [FakeProvider("kilo", error=ProviderError("down", retryable=True))]
    router = ModelRouter(FakeLocalService(loaded=True, text="local answer"), make_settings(), providers=providers)
    result = router.complete([{"role": "user", "content": "hello"}], max_tokens=16)
    assert result["qwendbc"]["provider"] == "local"


def test_invalid_bearer_token_is_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "expected")
    response = client.post(
        "/api/v1/chat/completions",
        headers={"Authorization": "Bearer wrong"},
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 401
```

- [ ] **Step 2: Run the focused tests and verify the correct red failures.**

```bash
PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_model_router.py backend/tests/test_access_control.py
```

Expected: FAIL because routing, auth, and limits are not present.

- [ ] **Step 3: Implement access control first.**

Create a small fixed-window limiter using a lock-protected dictionary with
bounded key cleanup. Derive the client key from the authenticated token hash
and `request.client.host`; do not trust arbitrary forwarding headers. Return
401 for missing/invalid bearer credentials and 429 with `Retry-After` when the
window or semaphore is exhausted. Apply the dependency to chat, model load,
model unload, catalog refresh, and document endpoints. Keep health public.

- [ ] **Step 4: Implement `ModelRouter` and local-provider bridge.**

Bridge the existing `LLMService` methods without changing their lifecycle
locking. Build remote providers from settings in this order: Kilo with
`https://api.kilo.ai/api/gateway` and `kilo-auto/free`, OpenCode with
`https://opencode.ai/zen/v1` and its free allowlist, OpenRouter with
`https://openrouter.ai/api/v1` and `openrouter/free`; append local. Cache each
catalog for a short TTL and expose configured/available state without keys.
For automatic non-streaming calls, try the configured order and attach
`qwendbc.provider`, `qwendbc.model`, `qwendbc.fallback`, and optional RAG source
metadata. For explicit selection, reject disabled/paid/non-text models. For
streaming, attempt the next provider only before the first content chunk; after
that point emit the existing generic SSE error and `[DONE]`.

- [ ] **Step 5: Add typed schemas and wire the API.**

Add optional `provider`, `model`, `use_rag`, and `rag_top_k` request fields.
Add typed provider/model catalog response classes and extend `HealthResponse`,
`ModelInfo`, and `ChatResponse` with non-secret fields while retaining current
required fields. Add `GET /api/v1/models` and protected
`POST /api/v1/models/refresh`. Chat uses the router for both routes; if
`use_rag` is true, search the last user message in a worker thread and inject
bounded labeled context before completion. Preserve the existing unloaded-local
400 behavior when no remote provider can serve the request. Keep the old fake
service dependency overrides working in existing tests.

- [ ] **Step 6: Run backend tests and repair only implementation defects.**

```bash
PYTHONPATH=backend .venv/bin/pytest -q backend/tests --cov=app --cov-report=term-missing
```

Expected: all backend tests pass, including existing local lifecycle and RAG
tests. Add explicit tests for catalog endpoint shape, protected document
mutation, no-token local compatibility, RAG prompt labeling, and stream
fallback-before-first-token.

- [ ] **Step 7: Commit the routing/API boundary.**

```bash
git add backend/app backend/tests
git commit -m "feat: route chat across free model providers"
```

## Task 4: Build tested theme and API client helpers

**Files:**
- Create: `frontend/src/theme.js`
- Create: `frontend/src/api.js`
- Create: `frontend/src/theme.test.js`
- Create: `frontend/src/api.test.js`
- Modify: `frontend/package.json`

**Interfaces:**
- `THEME_OPTIONS = ["day", "night", "system"]`.
- `readThemePreference(storage = window.localStorage) -> "day" | "night" | "system"`.
- `resolveTheme(preference, prefersDark) -> "day" | "night"`.
- `saveThemePreference(preference, storage = window.localStorage) -> void`.
- `applyTheme(preference, root = document.documentElement, prefersDark = ...) -> "day" | "night"`.
- `apiRequest(path, options = {}) -> Promise<Response JSON>` rejects with a
  safe `ApiError` containing `status` and user-safe `message`.
- `fetchModels()` and `fetchHealth()` use `VITE_API_URL || "/api/v1"`.
- `parseCompletion(response)` validates the assistant content shape.

- [ ] **Step 1: Add the smallest frontend test runner and write red helper tests.**

Configure Vitest with a jsdom environment only if necessary; otherwise use
Node-compatible helper tests with injected storage/root objects. Add tests:

```javascript
test("system preference resolves to the current OS theme", () => {
  expect(resolveTheme("system", true)).toBe("night");
  expect(resolveTheme("system", false)).toBe("day");
});

test("invalid stored theme falls back to system", () => {
  const storage = { getItem: () => "neon" };
  expect(readThemePreference(storage)).toBe("system");
});

test("applyTheme updates the root data attribute", () => {
  const root = { dataset: {} };
  expect(applyTheme("night", root, false)).toBe("night");
  expect(root.dataset.theme).toBe("night");
});
```

- [ ] **Step 2: Run the frontend tests and verify they fail for missing helpers.**

```bash
cd frontend && npm test -- --run src/theme.test.js
```

Expected: FAIL because the helper module and test script do not exist.

- [ ] **Step 3: Implement pure theme helpers and API utilities.**

Use `try/catch` around storage reads/writes, install one `matchMedia`
`change` listener from `App`, and write only `data-theme` to the root. API
helpers add the configured bearer token only when the user has provided it in
the runtime UI/configuration path; never hard-code a token into the bundle.
Parse JSON errors into actionable generic text and parse SSE lines without
assuming every event is JSON.

- [ ] **Step 4: Run helper tests and lint.**

```bash
cd frontend && npm test -- --run src/theme.test.js src/api.test.js && npm run lint
```

Expected: focused tests and oxlint pass.

- [ ] **Step 5: Commit tested client helpers.**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/theme.js \
  frontend/src/api.js frontend/src/theme.test.js frontend/src/api.test.js
git commit -m "feat: add theme and model API helpers"
```

## Task 5: Implement the premium responsive chat interface

**Files:**
- Replace: `frontend/src/App.jsx`
- Replace: `frontend/src/App.css`
- Modify: `frontend/src/main.jsx` if pre-paint initialization is used
- Test: `frontend/src/App.test.jsx` if the selected runner supports React/jsdom

**Interfaces:**
- App state includes `messages`, `input`, `isLoading`, `modelStatus`,
  `catalog`, `selectedProvider`, `selectedModel`, `themePreference`, and a
  user-safe `notice`.
- `sendMessage()` sends the current conversation plus optional provider/model
  and preserves prior messages when the request fails.
- `loadModel()` keeps the local lifecycle endpoint available.
- `selectTheme(preference)` saves and applies the preference immediately.

- [ ] **Step 1: Write a failing rendered behavior test or browser smoke.**

Assert the rendered app exposes all three theme choices, a model selector,
the chat composer, and an accessible status region. If no React test runner is
present, add a Playwright smoke command using the already-running Vite app and
record the expected selectors before changing JSX.

- [ ] **Step 2: Run the rendered test and verify it fails against the current UI.**

Run either:

```bash
cd frontend && npm test -- --run src/App.test.jsx
```

or, for the browser path:

```bash
npx playwright test --grep "theme and model controls"
```

Expected: FAIL because current UI has no theme selector or provider catalog.

- [ ] **Step 3: Replace the JSX with composed, accessible UI.**

Use semantic `header`, `main`, `section`, `aside`, and `footer`; labels for
selects/textarea; live regions for health and fallback notices; buttons with
text/tooltips and 44px targets. Load health and catalog in parallel with
`Promise.all`, cancel state updates on unmount, and do not block chat on catalog
failure. Allow chat when a remote provider is available or local Qwen is loaded;
show **Load local model** only when local fallback is needed. Render provider,
model, and fallback metadata from the backend without raw errors. Keep Enter to
send and Shift+Enter for a newline.

- [ ] **Step 4: Replace CSS with the intentional visual system.**

Use a refined editorial/technical direction: warm paper day mode, ink/navy
night mode, one electric cyan accent, amber status accent, subtle grid/grain
backgrounds, compact monospace metadata, and a distinctive display treatment
for the QwenDBC mark. Define all colors, surfaces, borders, radii, spacing, and
shadows as variables. Start with one-column mobile layout, enhance at 768px
and 1024px using fluid `minmax()`/`clamp()` values, prevent horizontal
overflow, and keep body text at least `1rem`. Add focus-visible styles and a
reduced-motion media query that removes transform/scroll animations.

- [ ] **Step 5: Run frontend tests, lint, and production build.**

```bash
cd frontend && npm test -- --run && npm run lint && npm run build
```

Expected: theme/model behavior passes, lint is clean, and Vite emits a
production bundle.

- [ ] **Step 6: Commit the frontend experience.**

```bash
git add frontend/src/App.jsx frontend/src/App.css frontend/src/main.jsx \
  frontend/src/App.test.jsx
git commit -m "feat: add premium responsive theme and model controls"
```

## Task 6: Document configuration and update release checks

**Files:**
- Modify: `README.md`
- Modify: `QUICKSTART.md`
- Modify: `docker-compose.yml` only if required by the tested configuration
- Modify: `Makefile` if a new frontend test command needs a named gate
- Modify: `.github/workflows/ci-cd.yml` only if the new gate is not covered

- [ ] **Step 1: Add documentation tests/checks first.**

Use a shell assertion that the example configuration contains every non-secret
provider variable and that the docs mention the exact fallback order and
authentication requirement:

```bash
for key in MODEL_MODE FREE_PROVIDER_ORDER REMOTE_MODELS_ENABLED \
  QWENDBC_ACCESS_TOKEN KILO_BASE_URL KILO_MODEL OPENCODE_BASE_URL \
  OPENCODE_FREE_MODEL OPENROUTER_BASE_URL OPENROUTER_MODEL; do
  rg -q "^${key}=" configs/.env.example
done
rg -q "kilo.*opencode.*openrouter.*local" README.md QUICKSTART.md
rg -q "QWENDBC_ACCESS_TOKEN" README.md QUICKSTART.md
```

Expected before the documentation change: at least one assertion fails.

- [ ] **Step 2: Update docs and Compose guidance.**

Document that `.env.ai` is never loaded automatically, show safe placeholder
configuration, explain that remote mode needs the bearer token, list catalog
and authenticated chat examples, describe day/night/system preference, and
give the rollback commands `MODEL_MODE=local` and
`REMOTE_MODELS_ENABLED=false`. Keep ports loopback by default and explicitly
state that public deployment requires an authenticated edge/app boundary.

- [ ] **Step 3: Run the documentation assertions and Compose validation.**

```bash
for key in MODEL_MODE FREE_PROVIDER_ORDER REMOTE_MODELS_ENABLED \
  QWENDBC_ACCESS_TOKEN KILO_BASE_URL KILO_MODEL OPENCODE_BASE_URL \
  OPENCODE_FREE_MODEL OPENROUTER_BASE_URL OPENROUTER_MODEL; do
  rg -q "^${key}=" configs/.env.example
done
rg -q "kilo.*opencode.*openrouter.*local" README.md QUICKSTART.md
rg -q "QWENDBC_ACCESS_TOKEN" README.md QUICKSTART.md
docker compose config --quiet
```

Expected: all assertions and Compose validation pass.

- [ ] **Step 4: Commit documentation/release configuration.**

```bash
git add README.md QUICKSTART.md configs/.env.example docker-compose.yml Makefile .github/workflows/ci-cd.yml
git commit -m "docs: document free provider deployment and themes"
```

## Task 7: Run full local verification and repair failures

**Files:**
- Modify only files implicated by fresh failing checks; preserve unrelated
  worktree changes.
- Test: all backend/frontend/Compose gates.

- [ ] **Step 1: Run the complete local gates from the repository root.**

```bash
make lint
make test
make security
make shellcheck
make docker-build
```

Also run the frontend production build independently after any frontend repair:

```bash
cd frontend && npm run build
```

- [ ] **Step 2: Reproduce every failure in isolation before editing.**

For each failure, capture the exact command, file/line, and smallest failing
test. Do not loosen assertions, skip providers, suppress lint, or change
security defaults to make the suite green.

- [ ] **Step 3: Apply one test-first repair per root cause.**

Add a regression test that fails for the reproduced behavior, run it red, make
the minimum implementation fix, run it green, then rerun the affected full
gate. Keep the remote default disabled and local behavior intact.

- [ ] **Step 4: Re-run all gates and inspect the final diff.**

```bash
git diff --check
git status --short --branch
git diff --stat origin/main...HEAD
```

Verify no secret-looking values, `.env.ai` contents, generated model files,
tokens, or unrelated files are staged. Verify each acceptance criterion in the
approved design against command output or a named test.

## Task 8: Deploy and verify `dbc.zeaz.dev` with bounded runtime checks

**Files/state:**
- Runtime-only QwenDBC `.env`/Compose environment; never commit secrets.
- No Terraform change unless read-only route inspection proves it is needed.

- [ ] **Step 1: Inspect runtime configuration without printing secrets.**

Check that the deployment has an app access token, intended provider keys, and
`REMOTE_MODELS_ENABLED=true` only in the operator environment. Report presence
and permissions, not values. If the token is absent, deploy in safe local mode
and leave remote mode disabled.

- [ ] **Step 2: Rebuild/restart only the QwenDBC stack.**

Use the repository's existing Compose/Make target with the deployment's
existing host-port variables, then wait for both containers to be healthy. Do
not stop unrelated services or alter Cloudflare/Terraform state.

- [ ] **Step 3: Verify local and authenticated API behavior.**

Run health and model/catalog checks while redacting all response fields except
status/provider/model IDs. Verify unauthenticated remote chat is 401 when the
token is configured, authenticated catalog returns only free text models,
provider fallback reaches local Qwen when remote providers are unavailable, and
SSE ends with `[DONE]`.

- [ ] **Step 4: Verify the public UI and responsive themes.**

Use the browser skill at `https://dbc.zeaz.dev` for read-only checks at mobile,
tablet, and desktop viewport sizes. Confirm day/night/system controls persist,
system mode follows a changed media preference, focus rings are visible, the
model selector and status are usable, and no internal path/key appears.

- [ ] **Step 5: Verify public routing and no-op infrastructure state.**

Check `https://dbc.zeaz.dev/api/v1/health`, the frontend HTML, and the existing
under-construction/status ownership only as read-only evidence. If a
Cloudflare/Terraform update is genuinely required, stop and produce a narrow
saved plan before any apply; otherwise leave the previously verified route
unchanged.

- [ ] **Step 6: Record deployment evidence and rollback readiness.**

Capture commit SHA, container health, local/API/public status codes, selected
provider/model, theme smoke result, and any unavailable provider. If runtime
behavior is unsafe or unhealthy, set `REMOTE_MODELS_ENABLED=false` or
`MODEL_MODE=local`, restart the QwenDBC stack, and re-run health before reporting
the final state.

## Final acceptance checklist

- [ ] Fresh local install works with only local GGUF settings.
- [ ] Kilo `kilo-auto/free` is attempted first when enabled.
- [ ] OpenCode dynamically selects an eligible current free model.
- [ ] OpenRouter uses exact `openrouter/free`, not paid `openrouter/auto`.
- [ ] Local Qwen is the final loaded-model fallback.
- [ ] No paid/media-only model is selected by automatic mode.
- [ ] Existing health, lifecycle, chat, streaming, documents, and search tests pass.
- [ ] API catalog, authentication, rate, and concurrency behavior are tested.
- [ ] Day/night/system themes persist and system mode follows OS changes.
- [ ] Mobile/tablet/desktop UI passes browser smoke and reduced-motion checks.
- [ ] Public hosted chat is authenticated and rate-limited.
- [ ] No secrets or generated artifacts are committed.
- [ ] Full local gates and public runtime evidence are recorded separately.
