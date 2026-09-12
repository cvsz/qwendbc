---
name: zok-execution-planning
description: zok execution-planning skill
---

# Execution Planning

## Purpose
Produce an executable, finite vertical-slice plan.

## Procedure
Translate requirements into acceptance criteria. Break work into ordered steps. Attach validation and rollback to each step. Identify which steps mutate state and which require approval. Estimate budget class (small/medium/large).

## Required outputs
Plan steps, acceptance criteria, risk matrix, validation matrix, stop condition.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
