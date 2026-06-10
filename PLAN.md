# Prism - Project Plan

## Architecture

```
fetch_pr → detect_languages → [parallel reviewers] → test_executor → aggregate → compare → HITL → output → storage
```

LangGraph graph with Send API for parallel reviewers, retry 3x per node, human-in-the-loop before posting to Bitbucket.

## Phases

### Core Infrastructure (Phases 1-6)
- [x] Phase 1: Core models (`app/core/models.py`)
- [x] Phase 2: Graph state (`app/graph/state.py`)
- [x] Phase 3: Config (`app/core/config.py`)
- [x] Phase 4: LLM client + prompts (`app/llm/`)
- [x] Phase 5: Bitbucket client (`app/bitbucket/client.py`)
- [x] Phase 6: Language detector (`app/graph/nodes/detect_languages.py`)

### Reviewers (Phases 7-12)
- [x] Phase 7: Base reviewer (`app/graph/nodes/reviewers/base.py`)
- [x] Phase 8: Python reviewer
- [x] Phase 9: Java reviewer
- [x] Phase 10: C++ reviewer
- [x] Phase 11: Ada reviewer
- [x] Phase 12: Docs reviewer

### Pipeline Nodes (Phases 13-18)
- [x] Phase 13: Test executor (`app/graph/nodes/test_executor.py`)
- [ ] Phase 14: Aggregate / AI Judge (`app/graph/nodes/aggregate.py`)
- [ ] Phase 15: Compare (`app/graph/nodes/compare.py`)
- [ ] Phase 16: Human approval (`app/graph/nodes/human_approval.py`)
- [ ] Phase 17: Output (`app/graph/nodes/output.py`)
- [ ] Phase 18: Storage (`app/storage/`)

### Integration (Phases 19-21)
- [ ] Phase 19: Graph builder (`app/graph/builder.py`)
- [ ] Phase 20: CLI (`app/cli.py`)
- [ ] Phase 21: Daemon (`app/daemon.py`)

### CI/CD & Quality
- [x] Ruff linting + formatting (line-length 120, Python 3.9)
- [x] Mypy type checking
- [x] Pytest with 90% coverage threshold
- [x] CodeQL code scanning
- [x] GitHub Actions CI
- [x] Docker build + health check
- [x] Pre-commit hooks

## Configurable LLM Models

Per reviewer node, configurable via `app/core/config.py` (env prefix `LLM_`):
- `LLM_PYTHON_REVIEWER_MODEL` — default: `gpt-4o`
- `LLM_JAVA_REVIEWER_MODEL` — default: `gpt-4o`
- `LLM_CPP_REVIEWER_MODEL` — default: `gpt-4o`
- `LLM_ADA_REVIEWER_MODEL` — default: `gpt-4o`
- `LLM_DOCS_REVIEWER_MODEL` — default: `gpt-4o`
- `LLM_JUDGE_MODEL` — default: `gpt-4o`
- `LLM_TEMPERATURE` — default: `0.3`

## Bitbucket Config

Env prefix `BB_`:
- `BB_URL` — default: `https://bitbucket.example.com`
- `BB_TOKEN` — required

## Test Config

Env prefix `PRISM_TEST_`:
- `PRISM_TEST_COVERAGE_THRESHOLD` — default: `80.0`
- `PRISM_TEST_FAIL_ON_COVERAGE_BELOW` — default: `true`
- `PRISM_TEST_FAIL_ON_TEST_FAILURE` — default: `true`
- `PRISM_TEST_TIMEOUT` — default: `300` (seconds)

Per-language thresholds:
```python
language_thresholds = {"python": 85.0, "java": 80.0, "cpp": 75.0, "ada": 70.0}
project_thresholds = {}  # override per project_key
```

## Storage Config

Env prefix `STORAGE_`:
- `STORAGE_DB_PATH` — default: `prism.db`
- `STORAGE_JSON_STORAGE_PATH` — default: `./reports`

## App Config

Env prefix `PRISM_`:
- `PRISM_HITL_ENABLED` — default: `true`
- `PRISM_RETRY_MAX_ATTEMPTS` — default: `3`
- `PRISM_LOG_LEVEL` — default: `INFO`

## Tech Stack

- Python 3.9.6
- LangGraph + LangChain
- Pydantic v2
- FastAPI + Uvicorn
- Ruff (lint + format)
- Mypy
- Pytest + Coverage
- CodeQL
- GitHub Actions
- Docker (multi-stage)
