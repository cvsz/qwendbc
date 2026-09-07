# Contributing to QwenDBC

Thank you for considering contributing to QwenDBC! We welcome contributions from the community and are grateful for your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a welcoming and inclusive community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/qwendbc.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Push to your fork: `git push origin feature/your-feature-name`
6. Open a Pull Request

## How to Contribute

### Types of Contributions We Welcome

- **Bug fixes**: Found a bug? We'd love a fix!
- **New features**: Have an idea? Let's discuss it first in an issue
- **Documentation improvements**: Help us make the docs better
- **Performance optimizations**: Make things faster
- **Security improvements**: Help us keep the project secure
- **Tests**: Add tests to improve coverage

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker and Docker Compose (optional, for containerized development)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development dependencies
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Running Locally

```bash
# Using Docker Compose
docker-compose up

# Or run separately
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
```

## Pull Request Process

1. **Create an Issue**: Before starting work on a significant change, please create an issue to discuss it
2. **Branch Naming**: Use descriptive branch names (e.g., `feature/add-auth`, `fix/login-bug`)
3. **Commit Messages**: Write clear, concise commit messages following [Conventional Commits](https://www.conventionalcommits.org/)
4. **Tests**: Ensure all tests pass and add new tests for new functionality
5. **Documentation**: Update documentation as needed
6. **Review**: Be responsive to code review feedback
7. **Squash Commits**: Squash related commits before merging

## Coding Standards

### Python

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints where possible
- Maximum line length: 127 characters
- Run linting before submitting: `flake8 .` and `mypy .`
- Format code with Black: `black .`

### JavaScript/TypeScript

- Follow ESLint configuration
- Use TypeScript for new code
- Maximum line length: 100 characters
- Run linting: `npm run lint`
- Format code: `npm run format`

### General

- Keep functions small and focused
- Write meaningful variable and function names
- Add comments for complex logic
- Avoid hardcoded values; use configuration

## Testing

### Backend Tests

```bash
cd backend
pytest --asyncio-mode=auto
pytest --cov=.  # With coverage
pytest -v       # Verbose output
pytest -m unit  # Run only unit tests
pytest -m "not slow"  # Skip slow tests
```

### Test Structure

Our test suite includes:
- **Unit Tests**: Test individual components (services, schemas, utilities)
- **Integration Tests**: Test API endpoints and database interactions
- **RAG Tests**: Test document upload and search functionality

Test files are located in `backend/tests/`:
- `test_main.py` - Core functionality tests
- `test_rag.py` - RAG pipeline tests

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Aim for high test coverage (but prioritize meaningful tests)
- Include unit tests, integration tests, and end-to-end tests as appropriate
- Mark slow tests with `@pytest.mark.slow` decorator

## Documentation

- Update README.md for significant changes
- Add docstrings to all public functions and classes
- Update API documentation if endpoints change
- Include examples for new features
- Keep CHANGELOG.md updated

## Reporting Bugs

Please use our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) when reporting bugs. Include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots or logs if applicable

## Suggesting Features

Use our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) to suggest features. Include:

- Problem description
- Proposed solution
- Alternative solutions considered
- Use cases

## Security

For security issues, please follow our [Security Policy](SECURITY.md) and **do not** create public issues for vulnerabilities.

## Questions?

Feel free to open an issue with questions or reach out to the maintainers.

Thank you for contributing! 🎉
