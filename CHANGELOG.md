# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- Updated chromadb to >=0.6.0 to address critical code injection vulnerabilities
- Updated llama-cpp-python to >=0.3.8 to fix remote code execution vulnerability
- Updated python-jose to >=3.5.0 to resolve algorithm confusion and DoS issues
- Updated python-multipart to >=0.0.20 to fix multiple DoS and file write vulnerabilities

### Added
- GitHub Actions CI/CD pipeline for automated testing and security scanning
- CodeQL analysis for continuous security monitoring
- Dependabot configuration for automated dependency updates
- Auto-merge workflow for Dependabot security patches
- Dependency review workflow to block vulnerable dependencies
- Issue templates for bug reports, feature requests, and security issues
- CODEOWNERS file for automatic reviewer assignment
- SECURITY.md with vulnerability reporting guidelines
- CONTRIBUTING.md with contribution guidelines
- CODE_OF_CONDUCT.md establishing community standards

### Changed
- Improved documentation structure

### Fixed
- Multiple critical and high severity security vulnerabilities in dependencies

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
