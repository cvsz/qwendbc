---
name: gemini-secrets
description: GCP Secret Manager integration: validate setup, fetch values, or confirm an NPM_TOKEN is non-revoked via `npm whoami`. Used for publish-time token rotation without long-lived keys in CI.
---

# gemini-secrets

> Codex skill for GCP Secret Manager — check / fetch / validate-token.

## Modes

### check
Validates the full GCP setup (`gcloud` on PATH, active project, auth principal, secret exists, WIF pool present). Use this when bootstrapping a new GCP project for publish.

```
/gemini-secrets mode=check
/gemini-secrets mode=check secret=NPM_TOKEN_DEV
/gemini-secrets mode=check project=my-gcp-project secret=NPM_TOKEN
```

### fetch
Fetches a secret value to stdout. Use in pipelines:

```
/gemini-secrets mode=fetch secret=NPM_TOKEN
/gemini-secrets mode=fetch secret=GH_TOKEN version=3
```

### validate-token
Fetches `NPM_TOKEN` and runs `npm whoami` against the registry. No publish — just confirms the token isn't revoked. Use this BEFORE you tag a release.

```
/gemini-secrets mode=validate-token
/gemini-secrets mode=validate-token secret=NPM_TOKEN_STAGING
```

## Equivalent CLI

```bash
gemini secrets check --secret=NPM_TOKEN
gemini secrets fetch NPM_TOKEN --version=3
gemini secrets validate-token
```

## Why this exists

So you can refresh + verify the publish-time GCP secret WITHOUT triggering a real publish.
