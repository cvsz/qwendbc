---
name: aicoder-aicoder
description: aicoder aicoder skill
---

```markdown
# aicoder Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill provides a comprehensive guide to the development patterns, coding conventions, and workflows used in the `aicoder` Python repository. It covers file organization, commit message standards, import/export styles, and common workflows for adding documentation and implementing new features with tests. This guide is intended for contributors looking to maintain consistency and quality in the project.

## Coding Conventions

- **Language:** Python
- **Framework:** None detected

### File Naming
- Use **kebab-case** for filenames.
  - Example: `repository-inventory.py`, `test-repository-inventory.py`

### Import Style
- Use **relative imports** within modules.
  - Example:
    ```python
    from .utils import parse_config
    ```

### Export Style
- Use **named exports** (i.e., define functions/classes explicitly for import).
  - Example:
    ```python
    def run_inventory():
        ...
    ```

### Commit Messages
- Follow **Conventional Commits**.
- Common prefixes: `docs`, `feat`, `test`
- Example:
  ```
  feat(scripts): add repository inventory script
  docs(audit): add security audit documentation
  test(repository-inventory): add tests for inventory script
  ```

## Workflows

### Add Audit Documentation
**Trigger:** When you need to document a new aspect of the project's audit or implementation status.  
**Command:** `/add-audit-doc`

1. Create a new markdown file under `docs/implementation/` with relevant audit or assessment content.
2. Commit the new file with a message like:
   ```
   docs(audit): add [topic] documentation
   ```
3. Example files:
   - `docs/implementation/repository-assessment.md`
   - `docs/implementation/dependency-map.md`
   - `docs/implementation/feature-matrix.md`
   - `docs/implementation/api-gap-analysis.md`
   - `docs/implementation/security-audit.md`
   - `docs/implementation/test-coverage-map.md`
   - `docs/implementation/file-implementation-plan.md`
   - `docs/implementation/change-log.md`
   - `docs/implementation/final-validation.md`

#### Example
```bash
echo "# API Gap Analysis" > docs/implementation/api-gap-analysis.md
git add docs/implementation/api-gap-analysis.md
git commit -m "docs(audit): add API gap analysis documentation"
```

---

### Feature Implementation with Test
**Trigger:** When adding a new script or feature and ensuring it is tested.  
**Command:** `/new-script-with-test`

1. Add the new script or feature file in the appropriate directory (e.g., `scripts/`).
2. Add a corresponding test file in `tests/`.
3. Commit each file with appropriate messages:
   - For the feature:  
     ```
     feat(scripts): add repository inventory script
     ```
   - For the test:  
     ```
     test(repository-inventory): add tests for inventory script
     ```
4. Example files:
   - `scripts/repository-inventory.py`
   - `tests/test-repository-inventory.py`

#### Example
```bash
# Add feature
touch scripts/repository-inventory.py
git add scripts/repository-inventory.py
git commit -m "feat(scripts): add repository inventory script"

# Add test
touch tests/test-repository-inventory.py
git add tests/test-repository-inventory.py
git commit -m "test(repository-inventory): add tests for inventory script"
```

## Testing Patterns

- **Framework:** Unknown (use standard Python testing patterns if unsure)
- **Test File Pattern:** Files are named with `.test.` in the filename, typically placed in a `tests/` directory.
  - Example: `tests/test-repository-inventory.py`
- **Test Structure:** Each feature or script should have a corresponding test file.
- **Example Test File:**
  ```python
  # tests/test-repository-inventory.py

  from scripts.repository_inventory import run_inventory

  def test_run_inventory_basic():
      result = run_inventory()
      assert isinstance(result, dict)
  ```

## Commands

| Command               | Purpose                                                      |
|-----------------------|--------------------------------------------------------------|
| /add-audit-doc        | Add new audit or assessment documentation under docs/         |
| /new-script-with-test | Implement a new feature/script along with its test coverage   |
```
