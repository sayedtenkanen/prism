---
name: ci-cd
description: GitHub Actions workflows, linting, testing, and CI/CD patterns. Use when user mentions "ci", "cd", "github actions", "workflow", "pipeline", "lint", "test". Triggers on CI/CD questions.
---

# CI/CD Conventions

## Prism CI Pipeline (GitHub Actions)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy app/

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
      - uses: github/codeql-action/init@v3
        with:
          languages: python
      - uses: github/codeql-action/analyze@v3

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t prism .
```

## Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    environment {
        PYTHON_VERSION = '3.12'
    }
    stages {
        stage('Setup') {
            steps {
                sh 'python${PYTHON_VERSION} -m venv venv'
                sh 'venv/bin/pip install -e ".[dev]"'
            }
        }
        stage('Lint') {
            steps {
                sh 'venv/bin/ruff check .'
                sh 'venv/bin/ruff format --check .'
                sh 'venv/bin/mypy app/'
            }
        }
        stage('Test') {
            steps {
                sh 'venv/bin/pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90'
            }
        }
        stage('Security') {
            steps {
                sh 'gitleaks detect'
            }
        }
        stage('Build') {
            steps {
                sh 'docker build -t prism .'
            }
        }
    }
}
```

## Local Pre-commit

```bash
ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```

## Branch Protection

- Direct push to `main` blocked (CodeQL blocks direct push)
- All changes via PRs
- CodeQL must pass before merge
- Ruff, mypy, pytest checks required

## Checklist

Before pushing:

```bash
ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```
