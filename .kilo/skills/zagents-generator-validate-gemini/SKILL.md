---
name: validate-gemini
description: Release-readiness umbrella check for a scaffolded gemini — runs doctor, witness verify, hardcoded-path scan, MCP server config, and GCP Secret Manager validation in one shot. Exits non-zero if any sub-check fails.
---

# validate-gemini

> Codex skill that runs the 5 release-readiness gates from `gemini validate`.

## What it checks

| # | Check | What it does |
|---|-------|--------------|
| 1 | `doctor` | File shape + manifest sha256 + at-least-one host artifact |
| 2 | `verify` | Witness manifest signature (Ed25519) — skipped if no witness yet |
| 3 | `path-guard` | Scans your TS/JS/Rust files for hardcoded `/tmp/`, `C:\`, `/Users/`, `/home/` — the original Windows `/tmp` bug regression class |
| 4 | `mcp` | `.mcp/servers.json` entries have `name` + `command` |
| 5 | `secrets` | `gcloud auth list` + project + `NPM_TOKEN` exist in GCP Secret Manager |

Each check reports `PASS` / `FAIL` / `WARN` with a one-line detail. Exits 1 if any FAIL.

## Usage from Codex

```
/validate-gemini
/validate-gemini path=./my-gemini
/validate-gemini path=./my-gemini skip_gcp=true
/validate-gemini secret=NPM_TOKEN_DEV
```

## Equivalent CLI

```bash
gemini validate ./my-gemini --skip-gcp --secret=NPM_TOKEN_DEV
```

## Why this exists

Before iter 20, you needed to remember to run `gemini doctor`, `gemini verify`, `gemini secrets check`, and `node scripts/path-guard.mjs` separately. This is the single release-readiness gate.
