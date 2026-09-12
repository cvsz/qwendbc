---
name: zasi-quantum-qec
description: >
  Simulate, calibrate, and verify Quantum Error Correction (QEC) codes including
  Surface Codes, Floquet Color Codes, and Hyperbolic Holographic codes within the
  ZASI Quantum Computation Engine.
---

# ZASI Quantum QEC Skill

Procedures and mathematical patterns for quantum error correction subsystems.

## Key Formulas & Invariants
- Code Distance: $d \ge 3$ for fault tolerance.
- Physical Error Threshold: $p_{\text{th}} \approx 1\%$ for 2D surface codes.
- Logical Invariant: $[X_L, Z_L] = 2i Y_L$.

## Usage Workflow
1. Execute `QuantumTeleportationMatrix` or `PlanetaryQuantumSensorMesh`.
2. Inspect syndrome extraction rounds.
3. Verify logical fidelity $F_L \ge 0.9999$.
