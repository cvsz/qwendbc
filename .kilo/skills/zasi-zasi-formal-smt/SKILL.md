---
name: zasi-formal-smt
description: >
  Construct and discharge First-Order Logic (FOL) invariants using SMT solvers (Z3 / CVC5)
  to guarantee safety, non-entropy divergence, and strict Plan A safety bounds.
---

# ZASI Formal SMT Verification Skill

Procedures for proving invariance of autonomous cognitive cycles.

## Verification Checklist
- [ ] Bounded state space: variables $\in [0.0, 1.0]$ or strictly typed domains.
- [ ] No division by zero or unbounded recursion in recursive upgrades.
- [ ] Pareto Dominance: New upgrade $U'$ must satisfy $\forall m \in \text{Metrics}, m(U') \ge m(U)$.
