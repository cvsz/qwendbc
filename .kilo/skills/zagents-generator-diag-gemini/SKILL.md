---
name: diag-gemini
description: Kernel-version skew check (ADR-027). Reports manifest surface + manifest kernel + installed kernel + verdict (match/patch-diff/minor-diff/major-diff). Exits 1 on minor/major skew with a copy-pasteable `npm install @metaharness/kernel@X.Y.Z` next step. Exits 2 if no .gemini/manifest.json at path.
---

# diag-gemini

> Codex skill: kernel-version skew check for a scaffolded gemini — the ADR-027 diagnostic UX loop.

## What it does

Single-question check: **does my local `@metaharness/kernel` match what this gemini was scaffolded against?** That's the cross-machine compatibility question almost every "this gemini doesn't work" support ticket turns out to be.

Reads `.gemini/manifest.json`:

| Field | Source | Meaning |
|---|---|---|
| `meta.surface` | iter 56 | Which surface produced the gemini (`cli` or `web-ui`) |
| `meta.kernel_version` | iter 58 | The `@metaharness/kernel` version stamped at scaffold time |

Resolves the local `@metaharness/kernel` via `createRequire` rooted at the gemini's own `package.json` (real Node resolution). Computes the skew verdict and prints a copy-pasteable next step.

| Verdict | Exit | Message |
|---|---|---|
| `match` | 0 | `PASS kernel versions match exactly` |
| `patch-diff` | 0 | `WARN patch-level skew (usually safe; may include bugfixes)` |
| `minor-diff` | 1 | `WARN minor-level skew (new kernel features may be missing)` + `Run: npm install @metaharness/kernel@X.Y.Z` |
| `major-diff` | 1 | `FAIL MAJOR skew — APIs may have changed; expect breakage` + `Run: npm install @metaharness/kernel@X.Y.Z` |
| no `.gemini/manifest.json` at path | 2 | `FAIL no .gemini/manifest.json found at this path` |

## Usage from Codex

```
/diag-gemini                           # cwd
/diag-gemini path=./my-gemini
```

## Equivalent CLI

```bash
gemini diag                            # cwd
gemini diag ./my-gemini               # explicit path
gemini diag ./my-gemini --json        # machine-readable for CI
gemini diag ./my-gemini --bundle      # support-ticket JSON (iter 90)
```

The `--bundle` form (iter 90) emits a single JSON snapshot of the diag report + sanitised manifest + `@metaharness/*` deps + Node/platform info — everything a maintainer needs to triage a bug report. Object keys matching `secret|token|key|password|api_key` are redacted so the bundle is safe to paste into a public GitHub issue.

## Sample output

```
gemini diag — checking /tmp/my-gemini

  surface:              cli
  manifest kernel:      0.1.0
  installed kernel:     0.1.0

  PASS kernel versions match exactly
```

## When to run

- After cloning someone else's gemini — first thing
- After bumping `@metaharness/kernel` in a gemini's `package.json`
- When `gemini doctor` fails with cryptic shape errors (skew is the usual cause)
- In CI before any other gemini subcommand — fail fast

## Lifecycle position

```
scaffold (create-agent-gemini)
    ↓
 your code lives in the gemini
    ↓
 diag (this skill)           <- before anything else, check compatibility
    ↓
 doctor / validate / sign / publish
```

## Related

- ADR-027 — CLI ↔ Web-UI integration (the parity contract diag enforces)
- iter 56 — `manifest.meta.surface` added
- iter 58 — `manifest.meta.kernel_version` stamped at scaffold time
- iter 66 — `gemini diag` subcommand
