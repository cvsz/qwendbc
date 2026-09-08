# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [Unreleased]

### Added

- Working local document ingestion and semantic-search endpoints backed by ChromaDB and sentence-transformers.
- Functional RAG API tests replacing skipped placeholder tests.
- Regression tests for model-unload races during normal and streaming inference.
- `backend/requirements-dev.txt`, `backend/pyproject.toml`, and coherent Black/Flake8/mypy/pytest configuration.
- Vite 8 frontend build, Nginx production serving, and same-origin `/api/` reverse proxy.
- Blocking frontend lint/build, Python dependency audit, Docker build, and conditional ShellCheck CI gates.
- npm Dependabot coverage for the frontend.
- Manual `workflow_dispatch` entry points for CI and CodeQL validation.

### Changed

- Migrated the frontend from Create React App / React 18 to Vite 8 / React 19.
- Moved the backend container to Python 3.13 for broad current AI-package compatibility.
- Updated core web/AI dependency floors to current compatible 2026 release lines.
- Split runtime and development Python dependencies.
- Updated Pydantic code to v2 APIs and strengthened request/config validation.
- Reworked synchronous llama.cpp streaming so it does not iterate on the ASGI event loop.
- Changed local development and Docker publishing to loopback-only defaults.
- Made Docker load the documented `.env` settings into the backend container while preserving container-specific model/vector paths.
- Raised the Nginx transport body ceiling above the backend upload limit and extended API proxy timeouts for slow model operations.
- Changed frontend chat requests to use backend generation defaults instead of hard-coded temperature/token values.
- Bounded frontend chat history to the backend's 128-message request limit.
- Modernized GitHub Actions majors and made release/test/build/audit failures blocking.
- Reworked ShellCheck jobs to scan only Git-tracked shell scripts.
- Rewrote README, contributor guidance, and Git sync documentation to match actual repository behavior.

### Fixed

- Replaced the invalid prose-only `.gitignore` with real ignore patterns.
- Removed the invalid self-referencing/dangling root `qwendbc` gitlink.
- Removed the tracked GGUF symlink pointing into another machine's Hugging Face cache.
- Stopped tracking the root `.env` while preserving a developer's local file during bundle application.
- Fixed Makefile test paths, missing coverage tooling, mutating lint behavior, and destructive cleanup targets.
- Fixed a model lifecycle race where inference could validate `self.model`, lose a race to unload, and then call a closed/cleared model reference.
- Serialized concurrent model load/unload operations so later lifecycle calls determine the final model state.
- Fixed invalid `MAX_TOKENS` configurations that could exceed `MAX_CONTEXT_LENGTH`.
- Prevented `.env` from overriding the source-controlled application version, eliminating another version-drift path.
- Fixed Docker configuration values from `.env` being used only for Compose interpolation instead of being passed into the backend container.
- Fixed Nginx's 1 MiB default body limit rejecting otherwise-valid document uploads.
- Fixed frontend HTTP success handling and deprecated keyboard event usage.
- Fixed frontend error handling so transport failures are not injected as fabricated assistant messages into future model context.
- Rolled back failed user turns and restored the draft input so failed requests do not enter later model history.
- Fixed the clear-chat race that could leave an orphan assistant reply after clearing during an in-flight request.
- Fixed invalid pytest configuration that used TOML syntax inside `pytest.ini`.
- Fixed `actions/first-interaction` input names and removed unnecessary checkout from the welcome workflow.
- Removed placeholder PyPI publishing and CI/release constructs that masked failures with successful exit codes.
- Replaced stale fork metadata (`@policedbc` CODEOWNERS/security links) with `@cvsz` / `cvsz/qwendbc`.
- Replaced the Code of Conduct's `[INSERT CONTACT METHOD]` placeholder with non-sensitive maintainer contact guidance.

### Security

- Removed unused authentication/secret configuration that implied protections the application does not implement.
- Bound Docker and development servers to loopback by default because both the backend and frontend `/api/` proxy are unauthenticated.
- Removed automatic Dependabot merging from the remediation set until `main` has required protected-branch checks.
- Added dependency auditing as a blocking CI and release step.
- Documented that `.env` removal does not erase or revoke any credential that may exist in Git history; exposed credentials must be rotated.

## [1.0.0] - 2024-01-01

### Added

- Initial FastAPI/llama.cpp chat application, React frontend, Docker configuration, and local model configuration.

[Unreleased]: https://github.com/cvsz/qwendbc/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/cvsz/qwendbc/releases/tag/v1.0.0
