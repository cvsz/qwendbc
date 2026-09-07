# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with unit tests for health endpoints, LLM service, chat router, and RAG functionality
- Pytest configuration with coverage reporting and test markers
- Test directory structure under `backend/tests/`
- GitHub Actions welcome workflow with proper permissions for first-interaction bot

### Security
- Fixed GitHub Actions welcome.yml permissions issue (403 Forbidden error)
- Added `issues: write` and `pull-requests: write` permissions for actions/first-interaction@v3
- Updated chromadb to >=0.6.0 to address critical code injection vulnerabilities
- Updated llama-cpp-python to >=0.3.8 to fix remote code execution vulnerability
- Updated python-jose to >=3.5.0 to resolve algorithm confusion and DoS issues
- Updated python-multipart to >=0.0.20 to fix multiple DoS and file write vulnerabilities

### Changed
- Improved documentation structure
- Enhanced CI/CD pipeline with test execution step

### Fixed
- Multiple critical and high severity security vulnerabilities in dependencies
- Welcome bot unable to post comments on first-time contributor issues and PRs

## [1.0.0] - 2024-01-01

### Added
- Initial release of QwenDBC
- FastAPI backend with LLM integration
- Vector database support with ChromaDB
- Frontend interface
- Docker containerization
- Authentication and authorization system

---

## Version Guidelines

### Version Numbering
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible new features
- **PATCH**: Backward-compatible bug fixes and security patches

### Sections
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements and vulnerability fixes

[Unreleased]: https://github.com/policedbc/qwendbc/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/policedbc/qwendbc/releases/tag/v1.0.0
