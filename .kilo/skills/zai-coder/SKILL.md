---
name: zai-coder
description: zai-coder skill
---

```markdown
# zai-coder Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns, coding conventions, and workflows used in the `zai-coder` Python repository. The project is organized for modularity and testability, with a focus on clear commit practices, consistent code style, and robust repository policies. You'll learn how to add new modules, expand test coverage, and harden the repository following established conventions.

## Coding Conventions

### File Naming
- Use **kebab-case** for files (e.g., `my-module.py`).

### Imports
- Use **relative imports** within modules.
  ```python
  from .utils import helper_function
  ```

### Exports
- Use **named exports** (explicitly listing what is available from a module).
  ```python
  # In zai_coder/core/my_module.py
  def important_function():
      pass

  __all__ = ["important_function"]
  ```

### Commit Messages
- Follow **conventional commit** format:
  - Prefixes: `chore`, `feat`, `test`, `refactor`, `docs`
  - Example: `feat: add user authentication module`

## Workflows

### Add New Module With Tests
**Trigger:** When adding a new core feature or subsystem with test coverage  
**Command:** `/new-module`

1. Create new implementation files in `zai_coder/core/`, `zai_coder/server/`, or a similar module directory.
   ```python
   # zai_coder/core/my_feature.py
   def do_something():
       return "done"
   ```
2. Add corresponding test files in `tests/` (e.g., `tests/test_my_feature.py`).
   ```python
   # tests/test_my_feature.py
   from zai_coder.core.my_feature import do_something

   def test_do_something():
       assert do_something() == "done"
   ```
3. Update `__init__.py` if you want to expose new imports or package namespaces.
   ```python
   # zai_coder/core/__init__.py
   from .my_feature import do_something
   __all__ = ["do_something"]
   ```

### Repository Hardening and Policy Update
**Trigger:** When improving repository security, readiness, or policy enforcement  
**Command:** `/harden-repo`

1. Update `.github/workflows/ci.yml` to add or modify CI steps.
2. Modify or add scripts in `scripts/repo/` and related directories.
   ```bash
   # scripts/repo/check-secrets.sh
   python zai_coder/github_ready_core/secret_scan.py
   ```
3. Update or add core policy/check modules (e.g., `repo_check.py`, `repo_policy.py`, `secret_scan.py`).
4. Add or update tests to cover new checks or policies.

### Test Expansion and Coverage
**Trigger:** When improving or ensuring test coverage for new or existing features  
**Command:** `/expand-tests`

1. Add or update test files in the `tests/` directory.
   ```python
   # tests/test_another_module.py
   from zai_coder.core.another_module import new_logic

   def test_new_logic():
       assert new_logic() is not None
   ```
2. Modify core logic files if needed to facilitate testing or fix test failures.
3. Run tests to verify coverage and correctness.

## Testing Patterns

- **Test files** are placed in the `tests/` directory and named as `test_<module>.py`.
- **Testing framework** is not explicitly specified, but tests follow standard Python `assert` patterns.
- Example test file:
  ```python
  # tests/test_example.py
  from zai_coder.core.example import example_func

  def test_example_func():
      assert example_func() == "expected"
  ```

## Commands

| Command        | Purpose                                                      |
|----------------|--------------------------------------------------------------|
| /new-module    | Add a new core module or subsystem with tests                |
| /harden-repo   | Harden repository, update CI, and enforce policies           |
| /expand-tests  | Add or expand tests to increase code coverage                |
```
