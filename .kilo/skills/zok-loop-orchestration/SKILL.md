---
name: zok-loop-orchestration
description: zok loop-orchestration skill
---

# Loop Orchestration

## Purpose
Run a bounded Discover → Plan → Execute → Verify → Repair feedback cycle.

## Procedure
1. Load goal, state, memory, permissions, and budgets.
2. Validate required configuration.
3. Run discovery.
4. Require a finite plan.
5. Execute approved actions.
6. Run independent verification and review.
7. If blocking failures exist, invoke bounded repair.
8. Detect no-progress/repeated failures.
9. Ship only after all required gates pass; otherwise hand off or terminate.

## Required outputs
`loop_state`, transition decision, evidence references, terminal reason.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
