---
name: zc-zc
description: zc zc skill
---

```markdown
# zc Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill introduces the core development patterns and conventions used in the `zc` Python codebase. It covers file naming, import/export styles, commit message practices, and testing patterns. These guidelines help maintain consistency and readability across the project.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `my_module.py`, `data_processor.py`

### Import Style
- Use **relative imports** within the codebase.
  - Example:
    ```python
    from .utils import helper_function
    ```

### Export Style
- Use **named exports** (explicitly define what is exported from a module).
  - Example:
    ```python
    def useful_function():
        pass

    __all__ = ['useful_function']
    ```

### Commit Patterns
- Commit messages are **freeform** but often start with a title.
- Average commit message length: ~75 characters.
  - Example:
    ```
    Add data processing utilities for CSV import
    ```

## Workflows

### Adding a New Module
**Trigger:** When you need to add new functionality to the codebase  
**Command:** `/add-module`

1. Create a new Python file using snake_case naming.
2. Implement your functionality.
3. Use relative imports to access shared utilities or modules.
4. Define `__all__` to specify exported functions/classes.
5. Write or update tests as needed.

### Updating an Existing Module
**Trigger:** When modifying or extending existing code  
**Command:** `/update-module`

1. Locate the module to update.
2. Make changes, following the import/export conventions.
3. Update `__all__` if new exports are added.
4. Update or add tests to cover new behavior.

### Writing a Commit
**Trigger:** When committing changes  
**Command:** `/commit`

1. Write a concise, descriptive commit message (preferably starting with a title).
2. Keep the message around 75 characters if possible.
3. Example:
    ```
    Refactor data_loader for improved error handling
    ```

## Testing Patterns

- **Framework:** Unknown (not detected)
- **Test file pattern:** `*.test.ts` (TypeScript test files)
- Tests are likely separated from Python source files and use the `.test.ts` suffix.
- Example test file: `my_module.test.ts`

## Commands
| Command         | Purpose                                      |
|-----------------|----------------------------------------------|
| /add-module     | Add a new Python module following conventions |
| /update-module  | Update an existing module                    |
| /commit         | Write a commit message following guidelines  |
```
