---
name: score-gemini
description: 5-dimension scorecard (0-100, grade A/B/C/F) for a scaffolded gemini. Dimensions: Repo understanding (25%), Agent usefulness (25%), MCP safety (20%), Test coverage (15%), Publish readiness (15%). Emits a 6-field badges block (score + mcpRisk + 4 booleans) ready for the gemini README. Exit 0 A/B, 1 C, 2 F.
---

# score-gemini

> Codex skill: 5-dimension gemini scorecard with README-ready badges
> (iter 111 → iter 114).

## What it does

Every generated gemini gets a single 0-100 score and a 6-field badge
block. The user roadmap target: **A grade (>=85) without manual edits.**

| Dimension | Weight | Reads |
|---|---|---|
| Repo understanding | 25% | `.gemini/manifest.json` (surface + kernel_version + host) |
| Agent usefulness | 25% | `src/agents/*.ts` + `.claude/skills/*` + `.claude/commands/*` counts |
| MCP safety | 20% | `.gemini/mcp-policy.json` (default-deny + audit + perm gates) |
| Test coverage | 15% | `__tests__/` + `npm test` + `.github/workflows/` |
| Publish readiness | 15% | `witness.json` + `sbom.json` + `package.json#bin` |

Grade + exit code:

| Grade | Range | Exit |
|---|---|---|
| **A** | 85-100 | 0 — the user's target |
| **B** | 70-84 | 0 |
| **C** | 50-69 | 1 (needs work) |
| **F** | 0-49 | 2 (blocked) |

## Badge block (the 6-field shape)

```json
{
  "score": 87,
  "mcpRisk": "Low",
  "releaseReady": true,
  "testsDetected": true,
  "sbom": true,
  "witnessSigned": true
}
```

`mcpRisk` is one of `None` / `Low` / `Medium` / `High`. Drop this block
into the generated gemini README as visible badges — see ADR-030 for the
propagation discipline.

## Usage from Codex

```
/score-gemini path=./my-gemini
/score-gemini path=./my-gemini bundle=true
```

## Equivalent CLI

```bash
gemini score ./my-gemini                # text + bars + dimension breakdown
gemini score ./my-gemini --json         # 6-field badges JSON
gemini score ./my-gemini --bundle       # ADR-031 schema-1 envelope
gemini score ./my-gemini --out badges.json
```

## Related skills

- `validate-gemini` (iter 22) — release-readiness umbrella that the
  score subcommand inherits signals from
- `diag-gemini` (iter 70) — kernel-version skew (one of the
  Repo-understanding signals)
- `threat-model` (iter 114) — focused MCP threat artifact

## See also

- [ADR-030](../../../docs/adrs/ADR-030-discovery-loop.md) · [ADR-031](../../../docs/adrs/ADR-031-bundle-json-pattern.md)
