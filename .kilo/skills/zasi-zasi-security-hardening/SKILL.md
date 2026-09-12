---
name: zasi-security-hardening
description: >
  Audit, sanitize, and harden ZASI codebase against CodeQL alerts, DOM XSS, secret exposure,
  API rate exhaustion, and insecure deserialization.
---

# ZASI Security Hardening Skill

Continuous security guidelines.

- Always verify Subresource Integrity (SRI) for all external CDN scripts.
- Never print or log sensitive field variables or cryptographic key streams in plain text.
- Enforce strict `permissions: contents: read` as the baseline across all GitHub Actions workflows.
