---
name: openapi-builder-openapi-builder
description: openapi-builder openapi-builder skill
---

```markdown
# openapi-builder Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill introduces the core development patterns and conventions used in the `openapi-builder` JavaScript codebase, which is built on the Express framework. You'll learn how to structure files, write imports/exports, and follow commit and testing conventions. This guide will help you contribute effectively and maintain consistency across the project.

## Coding Conventions

### File Naming
- Use **camelCase** for all file names.
  - Example: `openApiBuilder.js`, `routeHandler.js`

### Import Style
- Use **relative imports** for modules within the project.
  - Example:
    ```javascript
    import utils from './utils';
    import routeHandler from '../handlers/routeHandler';
    ```

### Export Style
- Use **default exports** for modules.
  - Example:
    ```javascript
    // In openApiBuilder.js
    const openApiBuilder = () => { /* ... */ };
    export default openApiBuilder;
    ```

### Commit Patterns
- Commit messages are **freeform** and may include prefixes, but there is no enforced structure.
- Average commit message length: **83 characters**.
  - Example:  
    ```
    Add support for custom parameter serialization in route builder
    ```

## Workflows

### Adding a New Feature
**Trigger:** When you want to introduce new functionality to the codebase  
**Command:** `/add-feature`

1. Create a new file using camelCase naming.
2. Implement your feature, using relative imports for dependencies.
3. Use default export for your module.
4. Write or update tests in a corresponding `*.test.*` file.
5. Commit your changes with a descriptive message.

### Fixing a Bug
**Trigger:** When you need to resolve a defect  
**Command:** `/fix-bug`

1. Identify the bug and locate the relevant file.
2. Make the necessary code changes.
3. Update or add tests to cover the bug fix.
4. Commit your changes with a clear message describing the fix.

### Running Tests
**Trigger:** To verify code correctness after changes  
**Command:** `/run-tests`

1. Locate all test files matching the `*.test.*` pattern.
2. Run the tests using the project's test runner (framework is unspecified; check project docs or package.json).
3. Review test output and address any failures.

## Testing Patterns

- Test files follow the `*.test.*` naming convention.
  - Example: `openApiBuilder.test.js`
- The specific testing framework is **unknown**; refer to project documentation or `package.json` for details.
- Place tests alongside the modules they test or in a dedicated `tests` directory, following the naming pattern.

## Commands
| Command       | Purpose                                         |
|---------------|-------------------------------------------------|
| /add-feature  | Start the workflow for adding a new feature     |
| /fix-bug      | Start the workflow for fixing a bug             |
| /run-tests    | Run all tests in the codebase                   |
```