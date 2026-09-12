---
name: zok-worktree-isolation
description: zok worktree-isolation skill
---

# Worktree Isolation

## Purpose
Prevent concurrent coding agents from overwriting one another.

## Procedure
Assign each mutating agent a unique branch/worktree. Define file ownership when practical. Sync from a known base revision. Merge only after verification. Detect overlapping diffs before integration.

## Required outputs
Workspace identifier, base revision, branch, changed files, integration status.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
