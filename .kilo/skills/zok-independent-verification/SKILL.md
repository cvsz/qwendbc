---
name: zok-independent-verification
description: zok independent-verification skill
---

# Independent Verification

## Purpose
Evaluate results independently from the agent that created them.

## Procedure
Map each acceptance criterion to at least one verification method. Prefer deterministic checks. Run the narrowest checks first, then broader regression checks. Return PASS/FAIL/INCONCLUSIVE per criterion.

## Required outputs
Verification matrix with command/check, result, evidence, failure classification.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
