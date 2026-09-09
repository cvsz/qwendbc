# API Reference

Complete API documentation for QwenDBC backend services.

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://chat.example.com/api/v1
```

## Authentication

Local development may run with an empty `QWENDBC_ACCESS_TOKEN`. When the token
is configured, the following routes require `Authorization: Bearer <token>`:
chat, model lifecycle/info, model catalog/refresh, and document upload/search.
`GET /health` and `GET /` remain readable for liveness and basic discovery.

Production configuration rejects an empty token and requires at least 32
characters. This is a single application access boundary, not multi-user
identity or tenant authorization. Put a production deployment behind TLS and
an identity-aware edge, and enforce distributed rate limits there.

## Endpoints

### Root

#### `GET /`

Returns basic application information.

**Response:**
```json
{
  "name": "Qwen LLM App",
  "version": "1.1.0",
  "docs": "/docs"
}
```

The `docs` field is omitted in production.

---

### Health Check

#### `GET /health`

Check the health status of the API and model.

**Response Schema:** `HealthResponse`

**Example Response:**
```json
{
  "status": "healthy",
  "version": "1.1.0",
  "model_loaded": true,
  "providers": [],
  "active_provider": null,
  "selected_model": null,
  "remote_models_enabled": false,
  "fallback_available": false,
  "timestamp": "2025-01-07T12:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is unhealthy

---

### Model Management

#### `GET /model/info`

Get information about the currently loaded model.

**Response Schema:** `ModelInfo`

**Example Response:**
```json
{
  "name": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
  "path": "/app/models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
  "context_length": 4096,
  "threads": 4,
  "loaded": true
}
```

**Status Codes:**
- `200 OK` - Model info retrieved
- `400 Bad Request` - Model not loaded
- `401 Unauthorized` - Missing or invalid bearer token when access is configured

---

#### `POST /model/load`

Load the LLM model into memory.

**Request Body:** None

**Example Response:**
```json
{
  "status": "loaded",
  "model": "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
}
```

**Possible Responses:**
- `{"status": "loaded"}` - Model successfully loaded
- `{"status": "already_loaded"}` - Model was already loaded

**Status Codes:**
- `200 OK` - Model loaded or already loaded
- `500 Internal Server Error` - Failed to load model
- `401 Unauthorized` - Missing or invalid bearer token when access is configured
- `429 Too Many Requests` - Process-local access limit exceeded

---

#### `POST /model/unload`

Unload the LLM model from memory to free resources.

**Request Body:** None

**Example Response:**
```json
{
  "status": "unloaded"
}
```

**Possible Responses:**
- `{"status": "unloaded"}` - Model successfully unloaded
- `{"status": "not_loaded"}` - Model was not loaded

**Status Codes:**
- `200 OK` - Model unloaded or not loaded
- `401 Unauthorized` - Missing or invalid bearer token when access is configured

---

### Chat Completions

#### `POST /chat/completions`

Generate a chat completion response.

**Request Schema:** `ChatRequest`

**Request Example:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 2048,
  "provider": "openrouter",
  "model": "openrouter/free",
  "use_rag": false,
  "rag_top_k": 5
}
```

**Response Schema:** `ChatResponse`

**Response Example:**
```json
{
  "id": "chatcmpl-550e8400-e29b-41d4-a716-446655440000",
  "object": "chat.completion",
  "created": 1704628800,
  "model": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 18,
    "total_tokens": 43
  }
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `messages` | array | Yes | - | List of chat messages |
| `temperature` | float | No | 0.7 | Sampling temperature (0.0-2.0) |
| `top_p` | float | No | 0.9 | Nucleus sampling parameter (0.0-1.0) |
| `max_tokens` | int | No | 2048 | Maximum tokens to generate (1-`MAX_CONTEXT_LENGTH`) |
| `provider` | string | No | configured route | Optional provider selection |
| `model` | string | No | configured route | Optional eligible model selection |
| `use_rag` | boolean | No | false | Add local retrieved context to the latest user message |
| `rag_top_k` | int | No | 5 | Number of local chunks to retrieve (1-50) |

**Message Format:**

Each message object contains:
- `role` (string): One of "system", "user", or "assistant"
- `content` (string): The message content

**Status Codes:**
- `200 OK` - Completion generated successfully
- `400 Bad Request` - Model not loaded or invalid request
- `401 Unauthorized` - Missing or invalid bearer token when access is configured
- `429 Too Many Requests` - Access or remote concurrency limit exceeded
- `503 Service Unavailable` - No provider is available or the document index is unavailable
- `500 Internal Server Error` - Generation failed unexpectedly

---

#### `POST /chat/completions/stream`

Generate a streaming chat completion response using Server-Sent Events (SSE).

**Request Schema:** `ChatRequest` (same as above)

**Request Example:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Tell me a story"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
```

**Response Format:** Server-Sent Events (SSE)

**Response Example:**
```
data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1704628800,"model":"Qwen/Qwen2.5-1.5B-Instruct-GGUF","choices":[{"index":0,"delta":{"content":"Once"},"finish_reason":null}]}

data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1704628800,"model":"Qwen/Qwen2.5-1.5B-Instruct-GGUF","choices":[{"index":0,"delta":{"content":" upon"},"finish_reason":null}]}

data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1704628800,"model":"Qwen/Qwen2.5-1.5B-Instruct-GGUF","choices":[{"index":0,"delta":{"content":" a"},"finish_reason":null}]}

data: [DONE]
```

**Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Status Codes:**
- `200 OK` - Stream started successfully
- `400 Bad Request` - Model not loaded
- `401 Unauthorized` - Missing or invalid bearer token when access is configured
- `429 Too Many Requests` - Access or remote concurrency limit exceeded before
  the SSE response starts
- `503 Service Unavailable` - No provider is available
- `500 Internal Server Error` - Streaming failed unexpectedly

After the SSE response starts, provider failures are represented by a safe
`data: {"error":"..."}` event followed by `data: [DONE]`; HTTP status cannot
be changed after streaming headers have been sent.

---

### Model Catalog

#### `GET /models`

Returns the normalized catalog of eligible free text-capable models and
provider availability. It is protected when access is configured and does not
return provider credentials.

#### `POST /models/refresh`

Refreshes remote provider catalogs using the configured timeout and returns the
same response shape as `GET /models`. Use this only from an authorized operator
session; provider failures are isolated and do not expose raw upstream errors.

### Document Retrieval

#### `POST /documents/upload`

Accepts a UTF-8 text multipart upload up to `MAX_UPLOAD_BYTES`, chunks it, and
stores normalized embeddings in the private SQLite RAG store. Returns the
filename and number of chunks added.

#### `POST /search`

Accepts `{ "query": "...", "top_k": 5 }` and returns local chunks ordered by
cosine distance. Both document routes are protected when access is configured.

### Data Models

### ChatMessage

```python
class ChatMessage(BaseModel):
    role: str          # "system", "user", or "assistant"
    content: str       # Message content
```

### ChatRequest

```python
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: float = 0.7                # 0.0 - 2.0
    top_p: float = 0.9                      # 0.0 - 1.0
    max_tokens: int = 2048                  # bounded by MAX_CONTEXT_LENGTH
    provider: Optional[str] = None
    model: Optional[str] = None
    use_rag: bool = False
    rag_top_k: int = 5                      # 1 - 50
```

### ChatResponse

```python
class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict
    qwendbc: Optional[dict]
```

### HealthResponse

```python
class HealthResponse(BaseModel):
    status: str           # "healthy" or "unhealthy"
    version: str
    model_loaded: bool
    timestamp: datetime
    providers: List[dict]
    active_provider: Optional[str]
    selected_model: Optional[str]
    remote_models_enabled: bool
    fallback_available: bool
```

### ModelInfo

```python
class ModelInfo(BaseModel):
    name: str
    path: Optional[str]
    context_length: int
    threads: int
    loaded: bool
    providers: List[dict]
    active_provider: Optional[str]
    selected_model: Optional[str]
    remote_models_enabled: bool
    fallback_available: bool
```

---

## Error Handling

All errors return a JSON response with the following format:

```json
{
  "detail": "Error message description"
}
```

### Common Error Codes

| Status Code | Meaning | Possible Causes |
|-------------|---------|-----------------|
| 400 | Bad Request | Model not loaded, invalid parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Internal Server Error | Model inference failure, system error |
| 503 | Service Unavailable | Service starting up, model loading |

---

## Rate Limiting

When access is configured, protected routes use a process-local fixed window
per token and client address. Remote provider calls also use a non-blocking
bounded semaphore. Limits are controlled by
`REMOTE_RATE_LIMIT_PER_MINUTE` and `REMOTE_MAX_CONCURRENT_REQUESTS`.

These limits are intentionally not a distributed quota system. A scaled or
public deployment must enforce identity, quotas, and abuse controls at the
edge or in shared infrastructure.

---

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) with the following default settings:

**Allowed Origins:**
- `http://localhost:3000`
- `http://127.0.0.1:3000`

**Allowed Methods:** `GET`, `POST`, and `OPTIONS`

**Allowed Headers:** `Authorization` and `Content-Type`

**Credentials:** Disabled

To customize CORS settings, modify the `ALLOWED_ORIGINS` environment variable.

---

## Interactive Documentation

FastAPI provides interactive API documentation in development:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- View request/response schemas
- Test endpoints directly
- Download OpenAPI specification

The production application disables `/docs`, `/redoc`, and `/openapi.json`.

---

## OpenAPI Specification

Download the OpenAPI specification:

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

Or access it directly in your browser:
http://localhost:8000/openapi.json

---

## Client Examples

### Python (requests)

```python
import requests

API_URL = "http://localhost:8000/api/v1"

# Load model
requests.post(f"{API_URL}/model/load")

# Send chat message
response = requests.post(
    f"{API_URL}/chat/completions",
    json={
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.7
    }
)

print(response.json()["choices"][0]["message"]["content"])
```

### JavaScript (fetch)

```javascript
const API_URL = "http://localhost:8000/api/v1";

// Load model
await fetch(`${API_URL}/model/load`, { method: "POST" });

// Send chat message
const response = await fetch(`${API_URL}/chat/completions`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: [{ role: "user", content: "Hello!" }],
    temperature: 0.7
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

### cURL

```bash
# Load model
curl -X POST http://localhost:8000/api/v1/model/load

# Chat completion
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

---

*Last updated: September 2026*
*Version: 1.1.0*
