---
name: GPTxCODEX-CONFIG-GPTxCODEX-CONFIG
description: GPTxCODEX-CONFIG GPTxCODEX-CONFIG skill
---

```markdown
# GPTxCODEX-CONFIG Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development conventions and workflows used in the GPTxCODEX-CONFIG TypeScript repository. You'll learn about file naming, import/export patterns, commit message styles, and how to structure and run tests. This guide is ideal for contributors aiming for consistency and best practices in this codebase.

## Coding Conventions

### File Naming
- Use **camelCase** for all file names.
  - Example: `configManager.ts`, `userSettings.test.ts`

### Import Style
- Use **relative imports** for all modules.
  - Example:
    ```typescript
    import { getConfig } from './configManager';
    ```

### Export Style
- Use **named exports** exclusively.
  - Example:
    ```typescript
    // configManager.ts
    export function getConfig() { ... }
    export function setConfig() { ... }
    ```

### Commit Messages
- Follow **Conventional Commits** with the `feat` prefix for new features.
  - Example:
    ```
    feat: add user settings support
    ```

## Workflows

### Adding a New Feature
**Trigger:** When implementing a new capability or module  
**Command:** `/add-feature`

1. Create a new TypeScript file using camelCase naming.
2. Implement your feature using named exports.
3. Import dependencies using relative paths.
4. Write corresponding tests in a `.test.ts` file.
5. Commit changes with a message like: `feat: describe your feature in 40 chars`
6. Open a pull request for review.

### Writing and Running Tests
**Trigger:** When adding or updating code  
**Command:** `/run-tests`

1. Create or update a test file matching `*.test.ts`.
2. Write tests for all new or changed functionality.
3. Use the project's test runner (framework unknown—consult project docs).
4. Run all tests and ensure they pass before committing.

## Testing Patterns

- Test files follow the `*.test.ts` naming pattern.
- Place tests alongside the modules they cover.
- Use the project's preferred (unspecified) test framework for assertions and test structure.

  Example:
  ```typescript
  // configManager.test.ts
  import { getConfig } from './configManager';

  describe('getConfig', () => {
    it('returns default config', () => {
      expect(getConfig()).toEqual({ ... });
    });
  });
  ```

## Commands
| Command      | Purpose                                  |
|--------------|------------------------------------------|
| /add-feature | Start the workflow for adding a feature  |
| /run-tests   | Run all tests in the project             |
```
