# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [Unreleased]

### Added

- Working local document ingestion and semantic-search endpoints backed by ChromaDB and sentence-transformers.
- Functional RAG API tests replacing skipped placeholder tests.
- `backend/requirements-dev.txt`, `backend/pyproject.toml`, and coherent Black/Flake8/mypy/pytest configuration.
- Vite 8 frontend build, Nginx production serving, and same-origin `/api/` reverse proxy.
- Blocking frontend lint/build, Python dependency audit, Docker build, and conditional ShellCheck CI gates.
- npm Dependabot coverage for the frontend.

### Changed

- Migrated the frontend from Create React App / React 18 to Vite 8 / React 19.
- Moved the backend container to Python 3.13 for broad current AI-package compatibility.
- Updated core web/AI dependency floors to current compatible 2026 release lines.
- Split runtime and development Python dependencies.
- Updated Pydantic code to v2 APIs and strengthened request/config validation.
- Reworked synchronous llama.cpp streaming so it does not iterate on the ASGI event loop.
- Modernized GitHub Actions majors and made release/test/build failures blocking.
- Rewrote README, contributor guidance, and Git sync documentation to match actual repository behavior.

### Fixed

- Replaced the invalid prose-only `.gitignore` with real ignore patterns.
- Removed the invalid self-referencing/dangling root `qwendbc` gitlink.
- Removed the tracked GGUF symlink pointing into another machine's Hugging Face cache.
- Stopped tracking the root `.env` while preserving a developer's local file during bundle application.
- Fixed Makefile test paths, missing coverage tooling, mutating lint behavior, and destructive cleanup targets.
- Fixed frontend HTTP success handling and deprecated keyboard event usage.
- Fixed invalid pytest configuration that used TOML syntax inside `pytest.ini`.
- Fixed `actions/first-interaction` input names and removed unnecessary checkout from the welcome workflow.
- Removed placeholder PyPI publishing and CI/release constructs that masked failures with successful exit codes.

### Security

- Removed unused authentication/secret configuration that implied protections the application does not implement.
- Removed automatic Dependabot merging from the remediation set until `main` has required protected-branch checks.
- Added dependency auditing as a blocking CI step.
- Documented that `.env` removal does not erase or revoke any credential that may exist in Git history; exposed credentials must be rotated.

## [1.0.0] - 2024-01-01

### Added

- Initial FastAPI/llama.cpp chat application, React frontend, Docker configuration, and local model configuration.

[Unreleased]: https://github.com/policedbc/qwendbc/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/policedbc/qwendbc/releases/tag/v1.0.0
