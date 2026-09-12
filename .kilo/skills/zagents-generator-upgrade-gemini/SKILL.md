---
name: upgrade-gemini
description: Drift detection + apply for a scaffolded gemini. Re-renders the template with the same vars, computes added/removed/changed file plan, and applies with Git-style conflict markers or .rej files. Default is dry-run.
---

# upgrade-gemini

> Codex skill: drift detection + apply for a scaffolded gemini.

## What it does

Re-renders the template that produced the gemini against the current generator version, using the same `vars` the original scaffold used. Computes a 3-bucket plan:

| Bucket | Meaning |
|---|---|
| **added** | upstream template now has files the gemini doesn't |
| **removed** | upstream template no longer has files the gemini does |
| **changed** | upstream and gemini differ; sub-classified `clean` vs `conflict` |

A **clean** change means the gemini's version equals the original generation — apply safely. A **conflict** means the user edited the file post-scaffold; the apply step writes either Git-style inline markers or a `.rej` sidecar for manual merge.

## Usage from Codex

```
/upgrade-gemini                                       # dry-run on cwd
/upgrade-gemini path=./my-gemini
/upgrade-gemini path=./my-gemini apply=true
/upgrade-gemini path=./my-gemini apply=true conflict=rej
```

## Equivalent CLI

```bash
gemini upgrade ./my-gemini                           # dry-run
gemini upgrade ./my-gemini --apply                   # apply, inline conflicts
gemini upgrade ./my-gemini --apply --conflict=rej    # apply, .rej sidecars
```

## Lifecycle position

```
scaffold (create-agent-gemini)
    ↓
 edit (you)
    ↓
 upgrade (this skill)   <- catches up to the latest template
    ↓
 sign / verify / publish
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | No drift OR clean apply (no conflicts) |
| 1 | Unresolved conflicts after apply, OR not a generated gemini, OR template missing |
| 2 | Bad `--conflict=` value |

CI workflows can gate on exit 1 to flag unresolved conflicts.
