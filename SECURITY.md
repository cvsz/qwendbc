# Security Policy

## Supported version

Security fixes are applied to the current `main` branch and the latest published release when practical. Older releases may not receive backports.

## Reporting a vulnerability

**Do not publish exploit details, credentials, private data, or reproduction steps in a public issue.**

Use GitHub's **Private Vulnerability Reporting** for this repository when the **Report a vulnerability** option is available under the Security tab. If private reporting is not enabled, open a public issue containing only a request for a private maintainer contact channel; do not include sensitive technical details in that issue.

A valid private report should include:

- affected version or commit;
- affected component and preconditions;
- impact assessment;
- minimal reproduction steps or proof of concept;
- suggested mitigation, if known.

Do not assume a specific response or remediation deadline unless a maintainer explicitly confirms one for the report.

## Current security boundary

QwenDBC is designed primarily for local/private use. The application currently provides:

- Pydantic request/config validation;
- explicit CORS origin configuration;
- local model execution;
- CodeQL, dependency review, Dependabot, `pip-audit`, and `npm audit` automation;
- non-root secret handling guidance through an ignored local `.env`.

The application **does not currently implement**:

- user authentication or authorization;
- API keys or access tokens;
- rate limiting;
- secure user sessions;
- tenant isolation.

Therefore, do not expose the FastAPI backend directly to an untrusted network. Put it behind an authenticated reverse proxy, VPN, zero-trust access layer, or equivalent control if remote access is required.

## Secret handling

Never commit `.env`, API keys, access tokens, private keys, or other credentials. If a real credential was committed at any point, removing it from the latest tree is insufficient: rotate/revoke the credential and assess whether Git history must be rewritten.

Local GGUF models and vector-store data may also contain sensitive or proprietary information and are intentionally ignored by Git.

## Dependency and model supply chain

- Review Dependabot and dependency-review findings before merging updates.
- Keep lockfiles committed where the ecosystem supports them.
- Review model repository provenance before changing `MODEL_NAME` / `MODEL_FILE`.
- Treat downloaded models and embedding models as third-party supply-chain artifacts.

## Security-related pull requests

Public pull requests may contain fixes **after** sensitive exploit details have been removed or coordinated privately. Do not embed secrets, active exploit payloads, or private-report content in public commits or CI logs.
