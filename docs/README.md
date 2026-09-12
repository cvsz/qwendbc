# AI-DBC Documentation

Welcome to the **AI-DBC** documentation. This project provides a local-first
AI chat solution using a Qwen GGUF model, with a FastAPI backend, React
interface, optional free-provider routing, and private document retrieval.

## 📚 Documentation Structure

### Core Documentation
- **[README.md](../README.md)** - Project overview, quick start, and features
- **[Architecture Overview](architecture/overview.md)** - System architecture and design decisions
- **[API Reference](api/README.md)** - Complete API documentation
- **[User Guide](user-guide/getting-started.md)** - End-user instructions
- **[Development Guide](development/setup.md)** - Developer setup and contribution guidelines
- **[Deployment Guide](deployment/docker.md)** - Production deployment instructions
- **[Security Guide](security/overview.md)** - Security policies and best practices

### Quick Links

#### For Users
- [Getting Started](user-guide/getting-started.md)
- [Chat Interface Usage](user-guide/chat-usage.md)
- [Troubleshooting](user-guide/troubleshooting.md)

#### For Developers
- [Development Setup](development/setup.md)

#### For DevOps
- [Docker Deployment](deployment/docker.md)

#### For Security Teams
- [Security Overview](security/overview.md)

## 🏗️ Project Overview

AI-DBC is a full-stack application that enables local AI chat capabilities using the Qwen language model. Key features include:

- **Local Execution**: Runs locally by default; remote providers are opt-in
- **Privacy First**: Local model, SQLite RAG data, and provider keys stay server-side
- **Modern Stack**: FastAPI backend + React frontend
- **Docker Support**: Easy deployment with Docker Compose
- **Streaming Responses**: Real-time token streaming
- **Model Management**: Load/unload models on demand
- **Controlled Routing**: Eligible free text models with local fallback

## 📋 System Requirements

### Minimum Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **OS**: Linux, macOS, or Windows with WSL2

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Storage**: SSD with 20GB+ free space
- **Network**: For initial model download only

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/cvsz/ai-dbc.git
cd ai-dbc

# Start with Docker Compose
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 📊 Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI    │────▶│  Llama CPP  │
│  Frontend   │◀────│   Backend    │◀────│   Python    │
│  (Port 3000)│     │  (Port 8000) │     │   Models    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ SQLite WAL  │
                    │  RAG store  │
                    └──────────────┘
```

## 🔧 Technology Stack

### Backend
- **Framework**: FastAPI
- **LLM Engine**: llama-cpp-python
- **RAG Store**: SQLite WAL with local cosine search
- **Embeddings**: sentence-transformers
- **Access Control**: optional bearer token; production-required
- **Validation**: Pydantic

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite
- **Styling**: CSS3
- **HTTP Client**: Fetch API

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Security**: CodeQL, Dependabot

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/cvsz/ai-dbc/issues)
- **Security Reports**: [SECURITY.md](../SECURITY.md)
- **Discussions**: [GitHub Discussions](https://github.com/cvsz/ai-dbc/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

*Last updated: September 2026*
