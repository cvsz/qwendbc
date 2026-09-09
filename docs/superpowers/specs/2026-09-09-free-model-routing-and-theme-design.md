# QwenDBC Free-Model Routing and Premium Theme

## Status

Approved rough design; awaiting spec review before implementation.

## Context

QwenDBC currently exposes a FastAPI backend and React frontend for one local
Qwen GGUF model. The public deployment at `dbc.zeaz.dev` is healthy, but chat
is currently coupled to the local `llama.cpp` service. The project does not
read the shared `/home/cvsz/.env.ai` file, has no hosted-model adapter, no
provider fallback, and no day/night/system theme preference.

The target is a full-stack, free-model-first experience that keeps the local
model and existing document/RAG functionality while adding Kilo, OpenCode,
and OpenRouter routing. Hosted provider credentials must remain server-side;
the public hostname must not become an unauthenticated proxy for provider
quotas.

## Goals

1. Support free text chat through these OpenAI-compatible provider contracts:
   - Kilo `kilo-auto/free` as the primary automatic free route.
   - OpenCode automatic selection from its current free catalog.
   - OpenRouter `openrouter/free` as a fallback router.
   - The existing local GGUF Qwen model as the final fallback when loaded.
2. Preserve the current synchronous and streaming chat API behavior for
   existing clients, while exposing provider/model selection for new clients.
3. Discover current free model catalogs without copying secret values or
   hard-coding a permanently stale list into the user interface.
4. Preserve model load/unload, health, model information, documents, RAG, and
   Docker/CI workflows.
5. Add a premium responsive interface with persisted `day`, `night`, and
   `system` themes, accessible controls, mobile support, and reduced-motion
   behavior.
6. Add safe defaults for public deployment: remote access is protected by a
   server-side bearer token and bounded request rate/concurrency controls.

## Non-goals

- Do not commit, print, or copy API keys from any `.env.ai` file.
- Do not treat paid models, OpenRouter `openrouter/auto`, OpenCode Go, or
  Kilo paid/credit routes as free.
- Do not remove the local GGUF model or require a hosted provider for local
  operation.
- Do not add user accounts, billing, multi-tenant persistence, or a distributed
  rate-limit service in this iteration.
- Do not automatically download or load the large local GGUF model during an
  arbitrary remote request.

## Provider architecture

### Contract

Introduce a provider interface behind the existing chat router. Each provider
implements:

- a health/configuration check;
- model catalog discovery;
- non-streaming chat completion;
- streaming chat completion;
- normalized provider/model metadata;
- safe error classification for retryable versus terminal failures.

The existing `LLMService` remains the local provider implementation. A new
OpenAI-compatible adapter is used by Kilo, OpenCode, and OpenRouter so request
formatting, SSE parsing, timeouts, and error normalization are shared rather
than duplicated.

### Provider configuration

Add settings to the application environment, with non-secret example values
in `configs/.env.example`:

```text
MODEL_MODE=auto_free
FREE_PROVIDER_ORDER=kilo,opencode,openrouter,local
REMOTE_MODELS_ENABLED=false
QWENDBC_ACCESS_TOKEN=
REMOTE_REQUEST_TIMEOUT_SECONDS=60
REMOTE_MAX_CONCURRENT_REQUESTS=4
REMOTE_RATE_LIMIT_PER_MINUTE=30

KILO_BASE_URL=https://api.kilo.ai/api/gateway
KILO_API_KEY=
KILO_MODEL=kilo-auto/free

OPENCODE_BASE_URL=https://opencode.ai/zen/v1
OPENCODE_API_KEY=
OPENCODE_FREE_MODEL=auto

OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free
```

The application reads the project `.env` and process environment only. The
shared `.env.ai` files are an operator reference, not an application input.
Deployment configuration may map already-authorized operator secrets into the
container environment without writing them into the repository.

`REMOTE_MODELS_ENABLED` defaults to `false`. Enabling it for the public
deployment requires `QWENDBC_ACCESS_TOKEN` to be non-empty. Provider keys are
optional for Kilo free access where anonymous access is supported, but the
application token remains required so the public service is not an open relay.

### Free-model rules

- Kilo accepts the explicit `kilo-auto/free` route and models whose catalog
  metadata has zero prompt and completion pricing and text output capability.
- OpenRouter accepts the explicit `openrouter/free` route and dynamically
  filters catalog entries with zero prompt and completion pricing and text
  output capability.
- OpenCode has no separate `auto/free` slug. `OPENCODE_FREE_MODEL=auto`
  selects the first available model from a maintained free-ID allowlist after
  refreshing the OpenCode catalog. The allowlist includes the current official
  free entries such as `big-pickle`, `mimo-v2.5-free`,
  `ling-3.0-flash-fin-free`, `nemotron-3-ultra-free`,
  `nemotron-3.5-lightning-free`, and contributor free models. The catalog is
  still checked at runtime so removed entries are not selected.
- Models that are media-only, paid, credit-based, or otherwise lack text chat
  capability are excluded even if their displayed price is zero.

### Automatic fallback

For `MODEL_MODE=auto_free`, the configured order is attempted once per
request. A provider is skipped when it is disabled, not configured, has no
eligible model, times out, returns a rate-limit response, or returns a 5xx
error. Authentication/configuration errors are recorded and skipped for the
remainder of that request. The final local provider is used only when its
model is already loaded.

For streaming requests, fallback is allowed until the first valid upstream
content chunk is sent to the client. Once output starts, the connection is
closed with the existing SSE error convention instead of silently switching
models mid-response. Non-streaming requests can retry the next provider when
the prior provider produced no usable response.

The response metadata records the selected provider and model. The frontend
shows when fallback occurred without exposing provider credentials or raw
upstream error bodies.

Explicit provider/model requests bypass automatic routing but still require
the provider to be enabled and the requested model to pass the provider's
free/text capability checks. The local load/unload endpoints retain their
current semantics.

## API changes

### Existing endpoints

Keep these routes backward compatible:

- `GET /api/v1/health`
- `GET /api/v1/model/info`
- `POST /api/v1/model/load`
- `POST /api/v1/model/unload`
- `POST /api/v1/chat/completions`
- `POST /api/v1/chat/completions/stream`
- existing document and RAG routes

Extend health/model information with non-secret active provider, selected
model, remote-enabled state, and fallback availability. Existing clients that
send only `messages` continue to work through the configured default mode.

### New endpoints

- `GET /api/v1/models`: returns normalized provider groups, eligible free
  models, availability/configuration status, and a short cache timestamp.
- `POST /api/v1/models/refresh`: refreshes provider catalogs for an authorized
  operator and returns the normalized result.

Chat requests gain optional `provider`, `model`, and `use_rag` fields. The
existing generation controls remain valid. RAG context is injected only when
requested (or when preserving the current document-aware behavior requires
it), with bounded context size and clear source metadata.

### Authentication and limits

Health can remain publicly readable. Model controls, catalog refresh, chat,
and document mutation routes require `Authorization: Bearer
QWENDBC_ACCESS_TOKEN` when the token is configured. The backend returns a
generic unauthorized response and never echoes the configured token.

Add a bounded in-process limiter keyed by authenticated token plus client
address, and a bounded semaphore for remote calls. Both limits are configurable
and return `429` with `Retry-After`. This protects the current single-backend
deployment; a future multi-replica deployment should move these controls to
Cloudflare or a shared store.

## Frontend experience

Replace the current one-state styling with a tokenized responsive design:

- `data-theme="day"` and `data-theme="night"` CSS variable sets;
- `system` preference resolved through `prefers-color-scheme` and updated when
  the OS preference changes;
- preference persisted in `localStorage`, with safe fallback if storage is
  unavailable;
- a three-option accessible theme control with visible selected state and
  keyboard support;
- responsive navigation/header, chat surface, composer, model status, and
  document/RAG panels that work on narrow screens;
- premium restrained color, spacing, elevation, typography, and focus tokens;
- `prefers-reduced-motion` disabling nonessential transitions/animations;
- provider/model selector, automatic-mode label, active-provider badge,
  fallback notice, loading/error/empty states, and retry affordance;
- no secret, raw upstream error, or internal filesystem path displayed.

The UI continues to use `VITE_API_URL` and remains compatible with the current
nginx `/api/` proxy. API failures are represented as actionable user-facing
states rather than uncaught promise errors.

## Verification strategy

Use test-first implementation for each behavior:

### Backend

- settings validation for provider URLs, free-mode defaults, token requirement,
  and numeric limits;
- catalog normalization and free/text filtering for each provider;
- OpenAI-compatible request/stream parsing and timeout/error mapping;
- fallback order, retry classification, explicit selection, and local final
  fallback;
- SSE output, first-chunk streaming boundary, and `[DONE]` behavior;
- authentication, rate limiting, concurrency bounds, and secret redaction;
- backward compatibility for existing local model and document/RAG tests.

### Frontend

- theme preference resolution and persistence for day/night/system;
- system preference change handling and reduced-motion-safe behavior;
- model catalog loading/selection, fallback messaging, and chat error states;
- existing lint and production build.

### Integration and release gates

- backend pytest, Black/Flake8/Mypy, pip-audit;
- frontend lint, component/theme tests, production build, npm audit;
- Docker Compose config/build and container health;
- authenticated local chat against mocked provider responses;
- read-only public health/model checks, then authenticated public chat smoke
  after deployment configuration is supplied;
- verify the public hostname does not expose provider keys, internal paths, or
  unauthenticated remote chat.

## Rollout and rollback

1. Implement behind `REMOTE_MODELS_ENABLED=false`, preserving local behavior.
2. Run the complete local gates and mocked provider integration tests.
3. Configure the deployment token and authorized provider settings outside Git.
4. Rebuild/restart the QwenDBC Compose stack and verify health, catalog, local
   fallback, authenticated remote chat, theme behavior, and public routing.
5. Roll back by setting `MODEL_MODE=local` or
   `REMOTE_MODELS_ENABLED=false` and restarting; no data migration is required.

## Acceptance criteria

- A fresh install remains usable with only the existing local model settings.
- With remote mode enabled and a valid access token, automatic mode tries the
  configured free-provider order and reports the actual selected provider.
- A provider outage/rate limit advances to the next configured free provider;
  local Qwen remains the final fallback when loaded.
- No paid model is selected by automatic free mode.
- Existing API/document/RAG behavior and CI gates remain green.
- Day, night, and system themes survive reload, follow OS changes in system
  mode, and remain usable on mobile and with reduced motion.
- Public `dbc.zeaz.dev` remote access is authenticated and rate-limited.
