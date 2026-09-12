---
name: zok-repair-loop
description: zok repair-loop skill
---

# Repair Loop

## Purpose
Correct verified failures with bounded retries.

## Procedure
Cluster failures by root cause. Choose the smallest repair that can address the highest-priority blocker. Apply one repair batch. Re-run affected verification. Compare with previous failure signature. Increment repair/no-progress counters.

## Required outputs
Repair diff/changes, root-cause hypothesis, new evidence, progress assessment.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
