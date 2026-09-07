name: Security Issue Report
description: Report a security vulnerability
title: "[Security]: "
labels: ["security", "critical"]
assignees:
  - octocat
body:
  - type: markdown
    attributes:
      value: |
        **Important:** For sensitive security issues, please consider contacting the maintainers directly via email before creating a public issue.
  - type: dropdown
    id: severity
    attributes:
      label: Severity Level
      description: How severe is this security issue?
      options:
        - Critical (Remote Code Execution, Data Breach)
        - High (Authentication Bypass, Privilege Escalation)
        - Medium (XSS, CSRF)
        - Low (Information Disclosure)
    validations:
      required: true
  - type: textarea
    id: description
    attributes:
      label: Vulnerability Description
      description: Describe the security issue in detail
      placeholder: Include steps to reproduce, affected components, and potential impact
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: Provide detailed steps to reproduce the vulnerability
      render: shell
    validations:
      required: true
  - type: input
    id: affected-version
    attributes:
      label: Affected Version(s)
      description: Which version(s) are affected?
      placeholder: ex. v1.0.0
    validations:
      required: true
  - type: checkboxes
    id: terms
    attributes:
      label: Code of Conduct
      description: By submitting this issue, you agree to follow our Code of Conduct
      options:
        - label: I agree to follow this project's Code of Conduct
          required: true
