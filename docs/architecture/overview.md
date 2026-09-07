# Architecture Overview

This document describes the architecture of QwenDBC, a local LLM full-stack application.

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              React Frontend (Port 3000)                  │    │
│  │  - Chat Interface                                        │    │
│  │  - Model Management UI                                   │    │
│  │  - Real-time Streaming                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              FastAPI Backend (Port 8000)                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │   Routers    │  │   Schemas    │  │   Services   │   │    │
│  │  │  - Chat      │  │  - Pydantic  │  │  - LLM       │   │    │
│  │  │  - Health    │  │  - Validation│  │  - RAG       │   │    │
│  │  │  - Model     │  │  - Config    │  │  - Utils     │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Function Calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Engine Layer                             │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │  llama-cpp-python│         │   ChromaDB       │              │
│  │  - Model Loading │         │  - Vector Store  │              │
│  │  - Inference     │         │  - Embeddings    │              │
│  │  - Streaming     │         │  - Similarity    │              │
│  └──────────────────┘         └──────────────────┘              │
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │ HuggingFace Hub  │         │ sentence-trans.  │              │
│  │  - Model Download│         │  - Embedding Gen │              │
│  └──────────────────┘         └──────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Model Files  │  │ Chroma DB    │  │ Logs         │          │
│  │ ./models     │  │ ./chroma_db  │  │ ./logs       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React)

**Location**: `/frontend/src`

**Key Files**:
- `App.js` - Main application component
- `index.js` - Entry point
- `App.css` - Styling

**Responsibilities**:
- User interface for chat interactions
- Model status monitoring
- Real-time message streaming
- Error handling and user feedback

**State Management**:
- React Hooks (useState, useEffect, useRef)
- Local state for messages, loading status, model status

### 2. Backend (FastAPI)

**Location**: `/backend`

#### Directory Structure
```
backend/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── app/
│   ├── __init__.py
│   ├── routers/         # API route handlers
│   │   ├── __init__.py
│   │   └── chat.py      # Chat endpoints
│   ├── schemas/         # Pydantic models
│   │   ├── __init__.py
│   │   ├── chat.py      # Chat schemas
│   │   └── config.py    # Configuration schema
│   ├── services/        # Business logic
│   │   ├── __init__.py
│   │   └── llm_service.py  # LLM management
│   └── utils/           # Utilities
│       ├── __init__.py
│       └── logger.py    # Logging configuration
```

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with app info |
| `/api/v1/health` | GET | Health check |
| `/api/v1/model/info` | GET | Get model information |
| `/api/v1/model/load` | POST | Load model into memory |
| `/api/v1/model/unload` | POST | Unload model from memory |
| `/api/v1/chat/completions` | POST | Generate chat response |
| `/api/v1/chat/completions/stream` | POST | Stream chat response |

### 3. LLM Service

**Singleton Pattern**: The LLMService uses singleton pattern to ensure only one model instance exists.

**Key Operations**:
1. **Model Download**: Downloads GGUF format models from HuggingFace
2. **Model Loading**: Loads model into RAM with optimized settings
3. **Message Formatting**: Formats messages in Qwen's chat template
4. **Inference**: Generates responses using llama-cpp-python
5. **Streaming**: Yields tokens in real-time
6. **Model Unloading**: Frees memory by unloading model

### 4. Data Flow

#### Chat Request Flow
```
1. User sends message via React frontend
2. Frontend makes POST request to /api/v1/chat/completions
3. FastAPI validates request using Pydantic schemas
4. Router calls llm_service.generate()
5. LLM Service formats messages for Qwen model
6. llama-cpp-python performs inference
7. Response formatted as OpenAI-compatible JSON
8. Response sent back to frontend
9. Frontend displays assistant message
```

#### Streaming Flow
```
1. User sends message (stream=true)
2. Backend returns StreamingResponse
3. Server-Sent Events (SSE) stream established
4. Tokens yielded one by one from model
5. Frontend updates UI in real-time
6. Stream ends with [DONE] marker
```

## Design Decisions

### 1. Local-First Architecture
- **Decision**: All processing happens locally
- **Rationale**: Privacy, no API costs, offline capability
- **Trade-off**: Requires more local resources

### 2. GGUF Model Format
- **Decision**: Use GGUF quantized models
- **Rationale**: Efficient CPU inference, smaller size
- **Trade-off**: Slight quality reduction vs full precision

### 3. Singleton LLM Service
- **Decision**: Single model instance per application
- **Rationale**: Memory efficiency, avoids duplicate loading
- **Trade-off**: Shared state across requests

### 4. Async/Await Pattern
- **Decision**: Use async for I/O operations
- **Rationale**: Non-blocking, better concurrency
- **Trade-off**: Complexity in error handling

### 5. Docker Compose
- **Decision**: Containerized deployment
- **Rationale**: Consistency, easy setup, isolation
- **Trade-off**: Slight overhead vs native

## Security Architecture

### Defense in Depth
1. **Network Layer**: CORS policies, port isolation
2. **Application Layer**: Input validation, rate limiting
3. **Data Layer**: Secure storage, access controls

### Key Security Features
- Environment-based configuration
- Secret key management
- Input sanitization via Pydantic
- CORS origin restrictions
- Health check endpoints for monitoring

## Scalability Considerations

### Current Limitations
- Single model instance (memory bound)
- No horizontal scaling
- No request queuing
- Limited concurrent users

### Future Improvements
- Model sharding for larger models
- Request queue with Redis
- Horizontal scaling with load balancer
- Caching layer for frequent queries
- Multi-model support

## Monitoring & Observability

### Logging
- Structured logging with levels
- Request/response logging
- Error tracking
- Performance metrics

### Health Checks
- Model loaded status
- API responsiveness
- Resource utilization

## Disaster Recovery

### Backup Strategy
- Model files: Re-downloadable from HuggingFace
- ChromaDB: Volume persistence
- Configuration: Version controlled

### Recovery Procedures
1. Container restart for transient issues
2. Model reload for inference failures
3. Volume restore for data corruption

---

*Last updated: January 2025*
*Version: 1.0.0*
