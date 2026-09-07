# API Reference

Complete API documentation for QwenDBC backend services.

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  http://your-domain.com/api/v1
```

## Authentication

Currently, the API does not require authentication for local deployment. For production use, implement JWT authentication using the `python-jose` library included in dependencies.

## Endpoints

### Root

#### `GET /`

Returns basic application information.

**Response:**
```json
{
  "name": "Qwen LLM App",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### Health Check

#### `GET /health`

Check the health status of the API and model.

**Response Schema:** `HealthResponse`

**Example Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
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
  "stream": false
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
| `max_tokens` | int | No | 2048 | Maximum tokens to generate (1-8192) |
| `stream` | boolean | No | false | Enable streaming response |

**Message Format:**

Each message object contains:
- `role` (string): One of "system", "user", or "assistant"
- `content` (string): The message content

**Status Codes:**
- `200 OK` - Completion generated successfully
- `400 Bad Request` - Model not loaded or invalid request
- `500 Internal Server Error` - Generation failed

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
- `500 Internal Server Error` - Streaming failed

---

## Data Models

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
    temperature: Optional[float] = 0.7      # 0.0 - 2.0
    top_p: Optional[float] = 0.9            # 0.0 - 1.0
    max_tokens: Optional[int] = 2048        # 1 - 8192
    stream: Optional[bool] = False
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
```

### HealthResponse

```python
class HealthResponse(BaseModel):
    status: str           # "healthy" or "unhealthy"
    version: str
    model_loaded: bool
    timestamp: datetime
```

### ModelInfo

```python
class ModelInfo(BaseModel):
    name: str
    path: str
    context_length: int
    threads: int
    loaded: bool
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

Currently, there is no rate limiting implemented for local deployments. For production use, consider implementing:
- Token bucket algorithm
- Request queuing
- Concurrent request limits

---

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) with the following default settings:

**Allowed Origins:**
- `http://localhost:3000`
- `http://127.0.0.1:3000`

**Allowed Methods:** All (`*`)

**Allowed Headers:** All (`*`)

**Credentials:** Allowed

To customize CORS settings, modify the `ALLOWED_ORIGINS` environment variable.

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- View request/response schemas
- Test endpoints directly
- Download OpenAPI specification

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

*Last updated: January 2025*
*Version: 1.0.0*
