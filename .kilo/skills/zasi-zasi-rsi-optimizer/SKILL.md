---
name: zasi-rsi-optimizer
description: >
  Perform safe 320x Recursive Self-Improvement (RSI) cycles, evaluate upgrade candidates,
  execute hot-swap bytecode runtime patching, and maintain immutable rollback journals.
---

# ZASI RSI Optimizer Skill

Safe autonomous self-improvement protocol.

## Step-by-Step Execution
1. Propose mutation via `RSIController.evaluate_candidate_upgrade(version)`.
2. Verify consensus in `DecentralizedDebateArena`.
3. Check Governor approval from `CognitiveSafetyGovernor`.
4. Hot-swap runtime with zero-downtime rollback journal.
