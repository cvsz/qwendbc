---
name: zaapi-dev
description: >-
  Use this skill when you need to run development workflows, rebuild production
  bundles, verify lint checks, or check directory and server configurations for
  the Zaapi copy-clone project.
---

# Zaapi Development Workflow Skill

This skill contains instructions and automation helpers for managing and verifying the Zaapi conversational commerce application clone.

## Available Actions

### 1. Verification and Lint Check
To verify if the codebase builds correctly without warnings or syntax errors, run the build-check script:
* Run command: `bash .agents/skills/zaapi-dev/scripts/build-check.sh`

### 2. Live Server Preview
To start the local Vite development server and expose the workspace URL for visual preview, run the dev preview helper script:
* Run command: `bash .agents/skills/zaapi-dev/scripts/run-dev.sh`

## Development Guidelines

1. **Vite Framework**: The project is structured as a React client-side bundle managed by Vite.
2. **Vanilla Styling**: All structural CSS overrides belong inside `src/index.css`.
3. **Sandbox Simulator**: Ensure any changes made to `UnifiedInbox.jsx` or `AIAgent.jsx` keep the simulated trigger structures operational so that test conversations still receive replies.
