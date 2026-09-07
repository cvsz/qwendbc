# GitHub Actions and repository rules

The repository workflows are intended to be blocking validation, not best-effort reporting.

## Recommended `main` ruleset

Enable a branch/ruleset for `main` with at least:

1. Require a pull request before merging.
2. Require the CI checks `backend`, `frontend`, `shellcheck`, and `docker-build`.
3. Require Dependency Review when it runs for the pull request.
4. Require CodeQL checks when GitHub code scanning is enabled.
5. Require the branch to be up to date before merging when appropriate for the repository workflow.
6. Block force pushes and branch deletion.
7. Apply the rules to administrators unless there is a documented break-glass process.

GitHub's displayed check names are authoritative; if workflow/job names change, update the required checks accordingly.

## Token permissions

Workflows declare least-privilege `GITHUB_TOKEN` permissions in their YAML. `GITHUB_TOKEN` is provided by GitHub and should not be created as a repository secret.

The current release workflow creates GitHub Releases only; it does not publish to PyPI or Docker Hub and therefore does not require placeholder PyPI/Docker credentials.

## Dependabot

Dependabot is configured for:

- Python dependencies in `/backend`;
- npm dependencies in `/frontend`;
- GitHub Actions;
- Docker images.

Automatic Dependabot merging is intentionally disabled in this remediation until `main` has required CI rules. Re-enable auto-merge only after protected checks are enforced.

## Security automation

- CodeQL runs for Python and JavaScript/TypeScript.
- Dependency Review blocks high-severity dependency changes according to its workflow policy.
- CI runs `pip-audit` and `npm audit` as blocking checks.

## Validation after applying repository rules

Open a test pull request and verify that GitHub blocks merging when any required job fails. Do not rely on a green workflow that suppresses command exit codes.
