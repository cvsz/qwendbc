# Git Sync Commands for QwenDBC

## Quick Sync Guide

### 1. **Fetch Latest Changes from Remote**
```bash
git fetch origin
```

### 2. **Rebase Your Branch on Latest Main**
```bash
git rebase origin/main
```

### 3. **Resolve Conflicts (if any)**
```bash
# If conflicts occur during rebase:
# 1. Edit conflicted files
# 2. Stage resolved files
git add <file>
# 3. Continue rebase
git rebase --continue
```

### 4. **Push to Remote**
```bash
# Force push after rebase (history rewritten)
git push --force-with-lease origin <your-branch-name>
```

---

## Complete Sync Workflow

```bash
# Step 1: Ensure you're on your branch
git checkout <your-branch-name>

# Step 2: Fetch latest from remote
git fetch origin

# Step 3: Rebase on latest main
git rebase origin/main

# Step 4: Resolve any conflicts (if they occur)
# - Edit conflicted files
# - git add <resolved-files>
# - git rebase --continue

# Step 5: Test your changes
cd backend && pytest

# Step 6: Push to remote (force with lease after rebase)
git push --force-with-lease origin <your-branch-name>
```

---

## Alternative: Merge Instead of Rebase

```bash
# If you prefer merging over rebasing:
git fetch origin
git merge origin/main
git push origin <your-branch-name>
```

---

## Check Status Commands

```bash
# Check current branch
git branch

# Check remote branches
git branch -a

# Check log
git log --oneline -10

# Check differences with main
git diff origin/main

# Check status
git status
```

---

## Undo Commands (If Something Goes Wrong)

```bash
# Abort rebase
git rebase --abort

# Reset to before rebase
git reflog
git reset --hard <commit-before-rebase>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

---

## Best Practices

1. **Always fetch before working**: `git fetch origin`
2. **Use rebase for clean history**: `git rebase origin/main`
3. **Force push with lease**: `git push --force-with-lease` (safer than --force)
4. **Test after rebase**: Run tests to ensure nothing broke
5. **Commit often**: Small, focused commits are easier to rebase
6. **Pull request early**: Get feedback before major changes

---

## Current Repository Status

- **Remote**: origin (https://github.com/policedbc/qwendbc.git)
- **Main Branch**: origin/main
- **Your Branch**: qwen-code-f3799129-69a6-42de-9889-bab0d972a280
- **Latest Commit**: feat: add comprehensive test suite and update documentation
- **Status**: ✅ Rebased on latest main, ready to push

---

## One-Liner Sync Command

```bash
git fetch origin && git rebase origin/main && git push --force-with-lease origin
```

⚠️ **Warning**: Only use the one-liner if you're confident there are no conflicts!
