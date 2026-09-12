---
name: zagents-generator-zagents-generator
description: zagents-generator zagents-generator skill
---

```markdown
# zagents-generator Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development conventions and workflows used in the `zagents-generator` TypeScript repository. You'll learn how to structure code, follow commit patterns, scaffold new packages, update the skill catalog, and enhance the Admin Control Panel (AdminCP) in the web UI. The guide also covers testing patterns and provides ready-to-use commands for common tasks.

## Coding Conventions

### File Naming
- Use **PascalCase** for file names.
  - Example: `MyComponent.ts`, `AgentGenerator.ts`

### Imports
- Use **relative import paths**.
  - Example:
    ```typescript
    import { Skill } from './Skill';
    ```

### Exports
- **Mixed export style**: both named and default exports are used.
  - Example:
    ```typescript
    // Named export
    export function generateAgent() { ... }

    // Default export
    export default AgentGenerator;
    ```

### Commit Patterns
- **Conventional commits** are used.
  - Prefixes: `feat`, `refactor`
  - Example:
    ```
    feat: add Gemini agent scaffolding
    refactor: improve skill import logic
    ```

## Workflows

### Update Skill Catalog
**Trigger:** When you want to add, import, or refactor skills/agents in the catalog.  
**Command:** `/update-skill-catalog`

1. Edit `packages/create-agent-gemini/templates/catalog.def.mjs` to add or update skills/agents.
2. Commit your changes with a message referencing "skills" or "catalog".
   - Example commit:  
     ```
     feat: update catalog with new summarization skill
     ```

### Add or Update AdminCP Feature
**Trigger:** When you want to add or enhance AdminCP functionality in the web UI (e.g., custom skills, agents).  
**Command:** `/add-admincp-feature`

1. Edit or create `apps/web-ui/src/components/AdminCP.tsx`.
2. Optionally update `apps/web-ui/src/App.tsx` to integrate AdminCP changes.
3. Commit your changes with a message referencing "AdminCP".
   - Example commit:  
     ```
     feat: add skill import UI to AdminCP
     ```

### Scaffold New Package
**Trigger:** When you want to scaffold a new feature or vertical as a package.  
**Command:** `/scaffold-package`

1. Create a new directory under `packages/` (e.g., `packages/agent-foo`).
2. Add the following files:
   - `LICENSE`
   - `README.md`
   - `package.json`
   - `tsconfig.json`
   - `src/index.ts`
   - `__tests__/*.test.ts`
   - Any templates or manifest files as needed (e.g., `templates/manifest.json`)
3. Commit all new files.
   - Example commit:  
     ```
     feat: scaffold agent-foo package
     ```

## Testing Patterns

- **Test files** use the pattern: `*.test.*` (e.g., `index.test.ts`).
- Testing framework is **unknown**, but tests are located in `__tests__` directories within each package.
- Example test file structure:
  ```
  packages/agent-foo/
    __tests__/
      index.test.ts
  ```

## Commands

| Command                | Purpose                                                      |
|------------------------|--------------------------------------------------------------|
| /update-skill-catalog  | Update or import skills/agents in the skill catalog          |
| /add-admincp-feature   | Add or enhance AdminCP features in the web UI                |
| /scaffold-package      | Scaffold a new package with initial files and configuration  |
```