---
name: ci-cd
description: GitHub Actions workflows, linting, testing, and CI/CD patterns. Use when user mentions "ci", "cd", "github actions", "workflow", "pipeline", "lint", "test". Triggers on CI/CD questions.
---

# CI/CD Conventions

## Prism CI Pipeline

```yaml
# .github/workflows/ci.yml
jobs:
  lint:
    - ruff check .
    - ruff format --check .
    - mypy app/
  test:
    - pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
  security:
    - gitleaks detect
    - codeql analysis
  build:
    - docker build
```

## Local Pre-commit

```bash
ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```

## Branch Protection

- Direct push to `main` blocked
- All changes via PRs
- CodeQL must pass before merge

## Checklist

Before pushing:

```bash
ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short
```
