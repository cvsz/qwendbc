---
name: zok-bounded-execution
description: zok bounded-execution skill
---

# Bounded Execution

## Purpose
Perform approved actions without expanding scope.

## Procedure
Create or select an isolated workspace. Execute one plan step at a time. Record outputs. Stop on unexpected destructive changes, permission errors, or invariant violations. Prefer reversible changes.

## Required outputs
Changed artifacts, action log, local validation evidence, unresolved errors.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
