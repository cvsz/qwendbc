# Git sync guide

This guide intentionally avoids hard-coded branch names, commit SHAs, or claims about the repository's current status.

## Update a feature branch from `main`

```bash
git fetch origin
git switch <your-branch>
git rebase origin/main
```

If conflicts occur, resolve them, stage the resolved files, and continue:

```bash
git add <resolved-files>
git rebase --continue
```

Abort safely if needed:

```bash
git rebase --abort
```

After a successful rebase, run the quality gates:

```bash
make lint
make test
make security
make docker-build
```

Push a rebased feature branch with lease protection:

```bash
git push --force-with-lease origin HEAD
```

Do not force-push shared protected branches such as `main`.

## Merge-based alternative

```bash
git fetch origin
git switch <your-branch>
git merge origin/main
make lint test
git push origin HEAD
```

## Useful status commands

```bash
git status --short --branch
git log --oneline --decorate -10
git diff origin/main...HEAD
git branch --all
```
