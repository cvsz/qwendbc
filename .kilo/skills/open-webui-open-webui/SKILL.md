---
name: open-webui-open-webui
description: open-webui open-webui skill
---

```markdown
# open-webui Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `open-webui` repository, a TypeScript codebase without a specific framework. You'll learn about file naming, import/export styles, commit message patterns, and how to structure and run tests. This guide also provides suggested commands for common workflows to streamline your development process.

## Coding Conventions

### File Naming
- **Style:** Snake case
- **Example:**  
  ```plaintext
  user_profile.ts
  api_client.ts
  ```

### Import Style
- **Style:** Relative imports
- **Example:**
  ```typescript
  import { fetchData } from './api_client';
  import { UserProfile } from '../models/user_profile';
  ```

### Export Style
- **Style:** Named exports
- **Example:**
  ```typescript
  // In user_profile.ts
  export function getUserProfile(id: string) { ... }
  export const DEFAULT_AVATAR = 'avatar.png';
  ```

### Commit Patterns
- **Type:** Freeform, with a title prefix
- **Example:**  
  ```
  fix: handle edge case in user profile loading
  feat: add support for dark mode in settings
  ```

## Workflows

### Adding a New Module
**Trigger:** When you need to add a new feature or module  
**Command:** `/add-module`

1. Create a new file using snake_case naming (e.g., `new_feature.ts`).
2. Use relative imports to include dependencies.
3. Export functions or constants using named exports.
4. Write corresponding tests in a `*.test.*` file.
5. Commit changes with a descriptive, title-prefixed message.

### Writing and Running Tests
**Trigger:** When you implement new logic or fix bugs  
**Command:** `/run-tests`

1. Create a test file matching the pattern `*.test.*` (e.g., `user_profile.test.ts`).
2. Write tests for your functions or modules.
3. Use the project's test runner (framework unknown; check project documentation or package.json for details).
4. Run tests and ensure all pass before committing.

## Testing Patterns

- **Test File Pattern:** Files should be named with the `*.test.*` pattern, e.g., `api_client.test.ts`.
- **Framework:** Not explicitly detected; check the repository for details.
- **Example:**
  ```typescript
  // In user_profile.test.ts
  import { getUserProfile } from './user_profile';

  test('should return user profile by id', () => {
    const profile = getUserProfile('123');
    expect(profile.id).toBe('123');
  });
  ```

## Commands
| Command        | Purpose                                   |
|----------------|-------------------------------------------|
| /add-module    | Scaffold and add a new module or feature  |
| /run-tests     | Run all tests in the codebase             |
```