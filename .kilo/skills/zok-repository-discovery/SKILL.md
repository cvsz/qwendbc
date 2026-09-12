---
name: zok-repository-discovery
description: zok repository-discovery skill
---

# Repository Discovery

## Purpose
Build the minimum repository context needed to make a correct plan.

## Procedure
Inspect project instructions first (`AGENTS.md`, README, architecture/roadmap/planning docs), then relevant source, tests, CI configuration, dependency manifests, and recent failure evidence. Avoid whole-repository dumping when targeted search is possible.

## Required outputs
Relevant file map, constraints, existing gates, failures, unknowns, dependencies.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
