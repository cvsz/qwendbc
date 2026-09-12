---
name: configure-sandbox
description: Analyze a workspace and create a Dockerfile for a sandboxed development environment. Use when users want to set up an isolated build environment. Triggers on requests like "create a sandbox", "create a dev container", "dockerize this workspace", "set up a development environment".
metadata:
  version: "0.1.0"
---

# Configure Sandbox

Analyze a workspace to identify its tech stack, then generate a Dockerfile for a sandboxed development environment.

## Workflow

### 1. Analyze Workspace

Identify project characteristics:

- **Language detection**: Check for `go.mod`, `package.json`, `Cargo.toml`, `pyproject.toml`, `requirements.txt`, `Gemfile`, `pom.xml`, `build.gradle`, `.sln`/`.csproj`
- **Build tools**: Look for `Makefile`, `CMakeLists.txt`, `BUILD`/`WORKSPACE` (Bazel), `Taskfile.yml`
- **Package managers**: `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `Cargo.lock`, `uv.lock`, `poetry.lock`
- **Tooling configs**: `.pre-commit-config.yaml`, `.golangci.yml`, `rustfmt.toml`, `.eslintrc.*`
- **Cloud/infra**: AWS (`aws/`, `samconfig.toml`), Docker (`docker-compose.yml`)

### 2. Determine Required Components

Map detected files to required tooling, e.g.,:

| Detected | Install |
|----------|---------|
| `go.mod` | Go, golangci-lint |
| `package.json` + `pnpm-lock.yaml` | Node.js, pnpm |
| `package.json` + `yarn.lock` | Node.js, yarn |
| `package.json` (other) | Node.js, npm |
| `Cargo.toml` | Rust (rustup) |
| `pyproject.toml` or `requirements.txt` | Python, uv |
| `BUILD`/`WORKSPACE` | Bazelisk |
| `.pre-commit-config.yaml` | pre-commit |
| AWS configs | AWS CLI |

### 3. Generate Dockerfile

Use the template in [references/dockerfile-template.md](references/dockerfile-template.md).

**Key requirements:**
- Base image: `ubuntu:24.04`
- Include `fuse-overlayfs` for overlay-fs support
- Multi-arch support via `TARGETARCH`
- Clean apt cache after installs
- Print versions at the end
- Workspace at `/workspace`

### 4. Output

Write `Dockerfile.dev` to the project's `docker/` directory (create if needed). Include build/run instructions as comments at the top.

### 5. Build the Image

After creating the Dockerfile, build the Docker image:

```bash
docker build -f docker/Dockerfile.dev -t <project>-dev:latest .
```

Where `<project>` is the name of the workspace directory (e.g., `my-app-dev:latest`).

### 6. Configure zAICoder Settings

Create or update `<workspace>/.zaicoder/settings.local.yaml` with the sandbox configuration:

```yaml
sandbox:
  image: <project>-dev:latest
  filesystem:
    workspaces:
      access: read-only
```

**Notes:**
- Create the `.zaicoder/` directory if it doesn't exist
- If `settings.local.yaml` already exists, merge the `sandbox` section with existing content. If there is a conflict, ask the user how to resolve it. Match indentation
- The `<project>` name should match the image tag used in step 5
