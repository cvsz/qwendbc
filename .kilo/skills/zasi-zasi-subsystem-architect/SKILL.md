---
name: zasi-subsystem-architect
description: >
  Scaffold, verify, test, and register new formal, physical, and omniversal
  subsystems (#177+) in the ZASI 176-subsystem architecture with First-Order SMT
  invariants and REST/WebSocket integration.
---

# ZASI Subsystem Architect Skill

Standard operating procedure for creating and registering new ZASI subsystems.

## Requirements for Any New Subsystem

1. **Structured Dataclass Report**: Every subsystem must return a typed `@dataclass` report.
2. **SMT Invariant Verification**: Must define mathematical bounds or non-violation invariants.
3. **No External Mandatory Dependencies**: Use Python stdlib or graceful optional fallbacks.
4. **Unit Test Coverage**: Add test case in `tests/test_all_subsystems.py`.
5. **REST API Registration**: Register in `backend/server.py` and `docs/SUBSYSTEMS_REFERENCE.md`.
