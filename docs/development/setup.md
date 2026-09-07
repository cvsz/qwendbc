# Development Setup Guide

This guide covers everything you need to start developing QwenDBC.

## Prerequisites

### Required Software

- **Python 3.10+** - Backend development
- **Node.js 18+** - Frontend development
- **Git** - Version control
- **Docker** (optional) - Containerized development

### Recommended Tools

- **VS Code** or similar IDE
- **Postman** or **Insomnia** - API testing
- **curl** - Command-line HTTP client

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/policedbc/qwendbc.git
cd qwendbc
```

### Step 2: Backend Setup

#### Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment

Create `.env` file in backend directory:

```bash
cp ../.env.example .env
```

Edit with your settings:

```env
# Application
APP_NAME=Qwen LLM App (Development)
DEBUG=True

# Model
MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct-GGUF
MODEL_FILE=qwen2.5-1.5b-instruct-q4_k_m.gguf
N_THREADS=4
MAX_CONTEXT_LENGTH=4096

# Security
SECRET_KEY=dev-secret-key-change-in-production

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### Run Backend Server

```bash
cd ..
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at http://localhost:8000

**Auto-reload** is enabled for development - changes restart automatically.

### Step 3: Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment

Create `.env` file in frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

#### Run Development Server

```bash
npm start
```

The frontend will start at http://localhost:3000

**Hot reload** is enabled - changes reflect immediately.

---

## Docker Development

### Development with Hot Reload

Create `docker-compose.dev.yml`:

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    container_name: qwen-backend-dev
    volumes:
      - ./backend:/app
      - ./models:/app/models
      - ./chroma_db:/app/chroma_db
    environment:
      - DEBUG=True
      - MODEL_NAME=${MODEL_NAME:-Qwen/Qwen2.5-1.5B-Instruct-GGUF}
    ports:
      - "8000:8000"
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    container_name: qwen-frontend-dev
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

Run development containers:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

---

## Code Structure

### Backend Structure

```
backend/
├── main.py                 # FastAPI application entry
├── requirements.txt        # Python dependencies
└── app/
    ├── __init__.py
    ├── routers/            # API route handlers
    │   ├── __init__.py
    │   └── chat.py         # Chat endpoints
    ├── schemas/            # Pydantic models
    │   ├── __init__.py
    │   ├── chat.py         # Chat schemas
    │   └── config.py       # Configuration
    ├── services/           # Business logic
    │   ├── __init__.py
    │   └── llm_service.py  # LLM management
    └── utils/              # Utilities
        ├── __init__.py
        └── logger.py       # Logging setup
```

### Frontend Structure

```
frontend/
├── package.json            # Node dependencies
├── public/
│   └── index.html          # HTML template
└── src/
    ├── index.js            # React entry point
    ├── App.js              # Main component
    └── App.css             # Styles
```

---

## Development Workflow

### Making Changes

1. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** to code

3. **Test locally**:
   - Backend: Run tests (see Testing section)
   - Frontend: Verify in browser

4. **Commit changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style

#### Backend (Python)

We use:
- **Black** for formatting
- **Flake8** for linting
- **Mypy** for type checking

Run formatters and linters:

```bash
# Format code
black backend/

# Lint code
flake8 backend/

# Type check
mypy backend/
```

#### Frontend (JavaScript)

We use:
- **ESLint** (via react-scripts)
- **Prettier** (recommended)

Run linter:

```bash
npm run lint
```

---

## Testing

### Backend Tests

Run all tests:

```bash
cd backend
pytest
```

Run specific test file:

```bash
pytest tests/test_chat.py
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html
```

### Frontend Tests

Run tests:

```bash
cd frontend
npm test
```

Run in watch mode:

```bash
npm test -- --watch
```

Run with coverage:

```bash
npm test -- --coverage
```

---

## Debugging

### Backend Debugging

#### Using print statements

```python
from app.utils.logger import get_logger
logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

#### Using pdb

```python
import pdb; pdb.set_trace()  # Breakpoint
```

#### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Frontend Debugging

#### Browser DevTools

- Open Chrome/Firefox DevTools (F12)
- Use Sources tab for breakpoints
- Console for logging

#### React DevTools

Install React DevTools extension for:
- Component tree inspection
- Props and state debugging
- Performance profiling

---

## API Development

### Adding New Endpoints

1. **Create schema** in `app/schemas/`:

```python
# app/schemas/example.py
from pydantic import BaseModel

class ExampleRequest(BaseModel):
    name: str
    value: int

class ExampleResponse(BaseModel):
    result: str
```

2. **Add router** in `app/routers/`:

```python
# app/routers/example.py
from fastapi import APIRouter
from app.schemas.example import ExampleRequest, ExampleResponse

router = APIRouter()

@router.post("/example", response_model=ExampleResponse)
async def example_endpoint(request: ExampleRequest):
    return {"result": f"Hello {request.name}"}
```

3. **Include router** in `main.py`:

```python
from app.routers import example

app.include_router(example.router, prefix="/api/v1", tags=["example"])
```

4. **Test endpoint** at http://localhost:8000/docs

---

## Database Development (ChromaDB)

### Local ChromaDB

For development, ChromaDB runs in-memory or persists to `./chroma_db`.

### Reset Database

```bash
rm -rf chroma_db/*
```

### Inspect Collections

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collections = client.list_collections()
print(collections)
```

---

## Model Development

### Testing Different Models

1. Update `.env`:
   ```env
   MODEL_NAME=Qwen/Qwen2.5-3B-Instruct-GGUF
   MODEL_FILE=qwen2.5-3b-instruct-q4_k_m.gguf
   ```

2. Clear old models:
   ```bash
   rm -rf models/*
   ```

3. Restart server

### Custom Model Templates

Modify message formatting in `llm_service.py`:

```python
def _format_messages(self, messages: List[Dict[str, str]]) -> str:
    # Custom formatting logic
    pass
```

---

## Performance Optimization

### Backend Optimization

1. **Use async/await** for I/O operations
2. **Batch operations** when possible
3. **Cache frequently used data**
4. **Profile with cProfile**:
   ```bash
   python -m cProfile -o output.prof main.py
   ```

### Frontend Optimization

1. **Use React.memo** for expensive components
2. **Debounce user input** for API calls
3. **Lazy load** non-critical components
4. **Profile with React DevTools**

---

## Common Development Tasks

### Add New Dependency

#### Backend

```bash
pip install package-name
pip freeze > requirements.txt
```

#### Frontend

```bash
npm install package-name
```

### Update Dependencies

#### Backend

```bash
pip install --upgrade -r requirements.txt
```

#### Frontend

```bash
npm update
```

### Clean Build Artifacts

```bash
# Backend
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Frontend
rm -rf node_modules build
```

---

## Contributing Guidelines

1. **Follow code style** (Black, ESLint)
2. **Write tests** for new features
3. **Update documentation** for changes
4. **Keep PRs small** and focused
5. **Pass CI checks** before merging

---

## Getting Help

- **Documentation**: `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/policedbc/qwendbc/issues)
- **Discussions**: [GitHub Discussions](https://github.com/policedbc/qwendbc/discussions)

---

*Last updated: January 2025*
*Version: 1.0.0*
