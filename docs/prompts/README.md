# AI-DBC Agentic Upgrade Prompt Pack

This directory contains the canonical high-level execution and review prompts for evolving AI-DBC from the current local-first QwenDBC/Cowork baseline into a secure agentic platform.

## Files

- [MASTER_EXECUTION.md](./MASTER_EXECUTION.md) — implementation program and architectural guardrails.
- [SECURITY_REVIEW.md](./SECURITY_REVIEW.md) — independent adversarial security review.
- [RELEASE_GATE.md](./RELEASE_GATE.md) — evidence-driven release verification.

## Recommended sequence

1. Run the master execution prompt against the latest repository state.
2. Run the security review with an independent reviewer/context.
3. Fix verified findings and rerun affected checks.
4. Run the release gate before merge or production claims.

## Repository-agent integration

The root `AGENTS.md` is the canonical entrypoint for agent work in this repository and points to this prompt pack.

PR #8 currently proposes tool-specific ECC files under `.codex`, `.claude` and `.agents`. Reconcile those files with this canonical policy instead of maintaining contradictory instructions.

## Evidence rule

Documentation is not implementation. A prompt, manifest, Docker build, deployment YAML, backup script or HA configuration is not runtime proof by itself. Use concrete code, tests, CI and operational evidence.
