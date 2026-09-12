---
name: zok-cost-governance
description: zok cost-governance skill
---

# Cost Governance

## Purpose
Keep agent loops affordable and predictable.

## Procedure
Track cumulative model/tool usage. Deduplicate context. Summarize completed stages. Use specialist agents only when their expected value exceeds cost. Block repeated identical attempts. Escalate before hard budget exhaustion when completion probability becomes low.

## Required outputs
Budget ledger, remaining allowance, governance decision, compression/escalation action.

## Safety / quality gates
- Operate within declared scope.
- Produce evidence for material claims.
- Never bypass stop conditions or permission boundaries.
- Update persistent loop memory after meaningful progress.
