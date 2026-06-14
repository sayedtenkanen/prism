# Prism - Agent Instructions

## Project Overview

AI-powered multi-language PR review tool using LangGraph + DSPy with SIA (Self-Improving Agent) feedback loops, running in Jenkins CI/CD or standalone CLI.

## Tech Stack

- Python 3.12
- DSPy 3.2 for LLM program optimization
- Pydantic v2 with `pydantic-settings`
- LangGraph for pipeline orchestration
- FastAPI + Uvicorn for API/daemon
- Ruff for linting and formatting
- Mypy for type checking
- Pytest + Coverage for testing

## Code Style

- **Line length**: 120 characters
- **Formatter**: Ruff (not Black)
- **Type hints**: Use native Python types (`list`, `dict`, `set`) — NOT `typing.List`, `typing.Dict`
- **Optional**: Use `Optional[X]` from typing (since `X | None` requires Python 3.10+)
- **Imports**: Sorted by Ruff isort rules
- **No comments**: Do not add comments unless explicitly requested

## Running Checks

Always run before committing:

```bash
ruff check .
ruff format --check .
mypy app/
pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```

## Project Structure

```
app/
├── core/           # Models, config
├── graph/          # LangGraph state, nodes
│   └── nodes/      # Pipeline nodes + reviewers
│       └── reviewers/  # Language-specific reviewers (base + concrete)
├── llm/            # LLM client, prompts
├── bitbucket/      # Bitbucket REST API client
├── storage/        # SQLite + JSON persistence
├── main.py         # FastAPI app
├── cli.py          # Click CLI (not yet implemented)
└── daemon.py       # APScheduler daemon (not yet implemented)
```

## Key Conventions

- All graph nodes are async functions
- Reviewers inherit from `BaseReviewer` and implement `language`, `system_prompt`, and `_build_user_prompt`
- `parse_llm_response` and `_parse_severity` are shared in `BaseReviewer` — do not duplicate in subclasses
- Severity comparison must use `ReviewSeverity.CRITICAL` enum, NOT string `"critical"`
- Config uses nested Pydantic models with `env_prefix` — see `app/core/config.py`
- `TestResult.evaluate()` only sets threshold/passed when coverage is not None
- Coverage thresholds: per-language defaults in `TestConfig.language_thresholds`, per-project overrides in `project_thresholds`
- SIA: Memory entries use `repo` as `{owner}/{repo}` format
- SIA: Feedback actions are `FeedbackAction` enum (accept/reject/modify)
- SIA: Dataset entries include `language`, `files_changed`, `diff`, `findings`, `feedback` fields
- SIA: Training datasets balanced by language using `DatasetBuilder.filter_by_language()`

## Testing

- Test files go in `tests/` mirroring `app/` structure
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Coverage threshold: 90% (enforced in CI)
- Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- **TDD skill**: Use `.opencode/skills/tdd/SKILL.md` for test-driven development workflow
