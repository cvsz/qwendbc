# Qwen LLM Full-Stack Application

Production-ready full-stack application for running Qwen LLM models locally on your hardware.

## Hardware Requirements Analysis

Based on your system specifications:
- **CPU**: Intel Xeon E3-1225 v5 (4 cores, 4 threads) @ 3.3GHz
- **RAM**: 16 GB DDR4-2126 (Single Channel) - *Limiting factor*
- **GPU**: Intel HD Graphics P530 (128 MB VRAM) - *No dedicated GPU*
- **Storage**: 1TB SSD (Samsung 870 QVO) + 2TB HDD

### Recommended Model Size
Given 16GB RAM with no dedicated GPU, we recommend:
- **Qwen2.5-1.5B-Instruct** (Best performance)
- **Qwen2.5-3B-Instruct** (Maximum size for smooth operation)

## Project Structure

```
qwen-llm-app/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── routers/        # Route handlers
│   │   ├── services/       # Business logic
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── utils/          # Utilities
│   ├── tests/              # Test suite
│   ├── requirements.txt    # Python dependencies
│   └── main.py             # Application entry point
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   ├── public/             # Static assets
│   └── package.json        # Node dependencies
├── docker/                 # Docker configurations
├── configs/                # Configuration files
├── docker-compose.yml      # Docker Compose
└── README.md               # This file
```

## Quick Start

### Using Makefile (Recommended)

```bash
# Full setup and run development servers
make setup && make dev

# Run tests before committing
make test && make lint

# Security check
make security

# Run with Docker
make docker-up

# See all available commands
make help
```

### Manual Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- Node.js 18+ (for frontend development)

### Installation

1. **Clone and setup**:
```bash
cd qwen-llm-app
```

2. **Configure environment**:
```bash
cp configs/.env.example configs/.env
# Edit configs/.env with your settings
```

3. **Start with Docker**:
```bash
docker-compose up --build
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features

- 🚀 **Local LLM Inference**: Run Qwen models entirely on your machine
- 💬 **Chat Interface**: Modern, responsive chat UI
- 📝 **Code Generation**: Specialized code assistance
- 🔍 **RAG Support**: Document upload and semantic search
- ⚡ **Optimized Performance**: Quantized models for CPU inference
- 🔒 **Privacy First**: All data stays on your machine
- 📊 **Monitoring**: Real-time resource usage tracking
- ✅ **Test Coverage**: Comprehensive pytest test suite with unit and integration tests
- 🔐 **Security Hardened**: CodeQL scanning, Dependabot updates, dependency review
- 🤖 **CI/CD Ready**: 8 GitHub Actions workflows for automated testing and deployment

## Configuration

Edit `configs/.env` to customize:
- Model selection and path
- Context window size
- Temperature and generation parameters
- API keys (if using external services)

## Performance Optimization

For your specific hardware:
1. Use GGUF quantized models (4-bit or 5-bit)
2. Set appropriate thread count (4 threads)
3. Enable memory mapping for large models
4. Use swap space if needed

## Testing

Run the test suite:

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_main.py -v

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m unit        # Run only unit tests
```

## Development

### Running Tests Locally
```bash
# Install test dependencies
pip install -r backend/requirements.txt
pip install pytest pytest-cov

# Run all tests
cd backend && pytest

# Run with verbose output
pytest -v --tb=short
```

## License

MIT License
