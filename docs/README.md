# QwenDBC Documentation

Welcome to the **QwenDBC** (Qwen Local LLM Full-Stack Application) documentation. This project provides a complete local AI chat solution using the Qwen language model, with both backend API and frontend interface.

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
- [Model Management](user-guide/model-management.md)
- [Troubleshooting](user-guide/troubleshooting.md)

#### For Developers
- [Development Setup](development/setup.md)
- [Code Structure](development/code-structure.md)
- [Testing Guide](development/testing.md)
- [API Development](development/api-development.md)

#### For DevOps
- [Docker Deployment](deployment/docker.md)
- [Environment Configuration](deployment/environment-config.md)
- [Monitoring & Logging](deployment/monitoring.md)
- [Backup & Recovery](deployment/backup-recovery.md)

#### For Security Teams
- [Security Overview](security/overview.md)
- [Vulnerability Management](security/vulnerability-management.md)
- [Access Control](security/access-control.md)
- [Data Privacy](security/data-privacy.md)

## 🏗️ Project Overview

QwenDBC is a full-stack application that enables local AI chat capabilities using the Qwen language model. Key features include:

- **Local Execution**: Runs entirely on your machine - no cloud dependencies
- **Privacy First**: All data stays on your device
- **Modern Stack**: FastAPI backend + React frontend
- **Docker Support**: Easy deployment with Docker Compose
- **Streaming Responses**: Real-time token streaming
- **Model Management**: Load/unload models on demand

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
git clone https://github.com/policedbc/qwendbc.git
cd qwendbc

# Start with Docker Compose
docker-compose up -d

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
                    │   ChromaDB   │
                    │  Vector DB   │
                    └──────────────┘
```

## 🔧 Technology Stack

### Backend
- **Framework**: FastAPI
- **LLM Engine**: llama-cpp-python
- **Vector Database**: ChromaDB
- **Embeddings**: sentence-transformers
- **Authentication**: python-jose (JWT)
- **Validation**: Pydantic

### Frontend
- **Framework**: React 18
- **Build Tool**: React Scripts
- **Styling**: CSS3
- **HTTP Client**: Fetch API

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Security**: CodeQL, Dependabot

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/policedbc/qwendbc/issues)
- **Security Reports**: [SECURITY.md](../SECURITY.md)
- **Discussions**: [GitHub Discussions](https://github.com/policedbc/qwendbc/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

*Last updated: January 2025*
*Version: 1.0.0*
