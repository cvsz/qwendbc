---
name: hermes-skill-author
description: Authors Hermes-compatible SKILL.md workflows.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, skills, skill.md]
    category: skills
    requires_toolsets: [terminal]
---

# Hermes Skill Author

## When to Use

Use this skill when you need to create, review, or refactor a reusable Hermes Agent `SKILL.md` workflow for ZAI Coder or another local-first agent environment.

## Procedure

1. Identify the concrete workflow the skill should teach.
2. Keep the frontmatter description short enough for catalog discovery.
3. Use this section order: `When to Use`, `Procedure`, `Pitfalls`, and `Verification`.
4. Put supporting material under `references/`, reusable outputs under `templates/`, helper code under `scripts/`, and supplementary files under `assets/`.
5. Declare platform limits only when the workflow truly depends on an operating system.
6. Declare required environment variable names, but never store secret values in the skill.
7. Prefer read-only or planning behavior by default; require explicit approval for state-changing operations.
8. Run the marketplace validator and security report before enabling the skill.

## Pitfalls

- Do not invent commands that the target project does not expose.
- Do not load broad reference material into the main `SKILL.md` when a focused reference file is enough.
- Do not request apply-level permissions such as `providers:apply` or `execution:apply` unless the workflow genuinely mutates state.
- Do not erase source provenance when importing from a hub, GitHub path, well-known endpoint, or direct URL.

## Verification

Confirm the skill is discoverable in the catalog, has a safe entrypoint, passes manifest validation, records source provenance, and only enables after the dry-run and approval gates pass.
