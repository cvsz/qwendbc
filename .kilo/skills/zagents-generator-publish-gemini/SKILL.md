---
name: publish-gemini
description: Publish a generated gemini to npm — runs the smoke test, signs the witness manifest, and dispatches `npm publish --provenance` from your tagged release.
---

# publish-gemini

> Codex skill that runs the full smoke-test → witness-sign → npm publish pipeline for a generated gemini.

## What it does

1. Builds the gemini with `npm run build`
2. Runs `npm test` to confirm green tests
3. Calls `gemini sign` to produce a fresh witness manifest (requires `WITNESS_SIGNING_KEY` env)
4. Confirms `gemini verify` accepts the freshly signed manifest
5. Either:
   - `dry_run=true` (default): runs `npm publish --dry-run` and reports tarball stats
   - `dry_run=false`: runs the real `npm publish --provenance --access public`

## Usage from Codex

```
/publish-gemini path=./my-gemini
/publish-gemini path=./my-gemini dry_run=false
```

## Equivalent CLI

```bash
cd ./my-gemini
npm run build
npm test
gemini sign
gemini verify
npm publish --provenance --access public
```

## Required env

- `WITNESS_SIGNING_KEY` — 64-hex-char ed25519 seed (fetch from GCP Secret Manager via `gemini secrets fetch WITNESS_SIGNING_KEY`)
- `NPM_TOKEN` — npm registry credential (Codex skill assumes the host has it set, or fetches via `gemini secrets fetch NPM_TOKEN`)

## See also

- `validate-gemini` — release-readiness gate (run this FIRST)
- `gemini-secrets` — manage GCP-stored signing/publishing tokens
