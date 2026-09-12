---
name: example-gemini
description: Scaffold a ready-made AI agent gemini in one command from the 19 published @metaharness/* example packages — 9 host integrations (Claude Code, Codex, Hermes, pi.dev, OpenClaw, RVM, Copilot, OpenCode, GitHub Actions) + 10 vertical pods (devops, research, trading, support, legal, coding, education, sales, gaming, repo-maintainer).
---

# example-gemini

One-command scaffolding from the 18 **published** `@metaharness/*` example
packages — the fastest path from a use-case to a working gemini, no
template/host flags to remember.

Where [`create-gemini`](../create-gemini/) walks the full wizard, this
skill maps a use-case straight onto a published npm wrapper. Each wrapper
shells out to `metaharness@latest` with the correct `--template` + `--host`
flags, so the result is byte-identical to the full CLI invocation.

## Install

```bash
mkdir -p ~/.codex/skills/example-gemini
curl -fsSL https://raw.githubusercontent.com/ruvnet/agent-gemini-generator/main/.codex/skills/example-gemini/skill.toml \
  -o ~/.codex/skills/example-gemini/skill.toml
```

No MCP server needed — the wrapper packages run via `npx`.

## Use

```
/example-gemini
```

Codex prompts for the package + a directory name, then runs:

```bash
npx --yes @metaharness/<package>@latest <name>
```

## The 18 packages

**Host integrations** (scaffold a workspace wired for one runtime)

| Package | Scaffolds |
|---|---|
| `@metaharness/claude-code` | Claude Code workspace + plugin |
| `@metaharness/codex` | OpenAI Codex |
| `@metaharness/hermes` | Hermes cli-config |
| `@metaharness/pi-dev` | pi.dev AGENTS.md |
| `@metaharness/openclaw` | OpenClaw `.openclaw/` |
| `@metaharness/rvm` | RVM deployment partition |
| `@metaharness/copilot` | VSCode / Copilot `mcp.json` |
| `@metaharness/opencode` | OpenCode `.opencode/` |
| `@metaharness/github-actions` | GitHub Actions CI/CD (non-interactive) |

**Vertical workflows** (ready-made multi-agent pods)

| Package | Scaffolds |
|---|---|
| `@metaharness/devops` | incident response |
| `@metaharness/research` | multi-source dossier |
| `@metaharness/trading` | quant trading (paper-by-default) |
| `@metaharness/support` | customer support |
| `@metaharness/legal` | contract redline (drafts only) |
| `@metaharness/coding` | engineering pod |
| `@metaharness/education` | tutor pod |
| `@metaharness/sales` | sales pipeline pod |
| `@metaharness/gaming` | game-design pod |
| `@metaharness/repo-maintainer` | OSS repo maintainer |

## After scaffolding

```bash
cd <name> && npm install
npx gemini doctor      # health-check
npx gemini validate    # full umbrella gate
```

Every scaffold ships a `.claude-plugin/plugin.json`, so it also loads as a
Claude Code plugin: `claude -p --plugin-dir <name> "..."`.

Per-package deep-dive gists: see
[`examples-packages/GISTS.md`](https://github.com/ruvnet/agent-gemini-generator/blob/main/examples-packages/GISTS.md).
