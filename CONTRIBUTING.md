# Contributing to Prism

## Setup

```bash
git clone https://github.com/sayedtenkanen/prism.git
cd prism
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Branch Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/phase-N-description main
   ```

2. Make changes, ensure all checks pass:
   ```bash
   ruff check .
   ruff format --check .
   mypy app/
   pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
   ```

3. Push and open a PR against `main`:
   ```bash
   git push -u origin feat/phase-N-description
   ```

**Note:** Direct push to `main` is blocked by CodeQL. All changes must go through PRs.

## Code Style

- **Line length:** 120 characters
- **Formatter:** Ruff (not Black)
- **Type hints:** Native Python (`list`, `dict`) — not `typing.List`
- **Optional:** `Optional[X]` from typing (not `X | None` for Python 3.9 compat)
- **No comments** unless explicitly requested
- **Async:** All graph nodes and agent methods are async

## Project Structure

```
app/
├── agents/           # DSPy agents, signatures, modules
│   ├── base.py       # BaseAgent + parse_findings
│   ├── signatures.py # DSPy Signatures
│   ├── modules.py    # Orchestrator, Debate, Judge, Pipeline
│   └── {security,performance,...}.py  # Specialized agents
├── graph/            # LangGraph pipeline
│   ├── state.py      # PRReviewState TypedDict
│   ├── builder.py    # Graph wiring
│   └── nodes/        # Pipeline nodes
├── rag/              # RAG store interface + PGVector
├── scm/              # SCM client protocol + GitHub
├── core/             # Config, models
├── llm/              # LLM client, prompts
└── main.py           # FastAPI app
```

## Testing

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Coverage threshold: 90% (enforced in CI)
- Async tests: `pytest-asyncio` with `asyncio_mode = "auto"`

## Adding a New Agent

1. Create a Signature in `app/agents/signatures.py`
2. Create an agent class in `app/agents/` inheriting from `BaseAgent`
3. Set `agent_name` and `self.review = dspy.ChainOfThought(YourSignature)`
4. Register in `ReviewOrchestrator.agents` in `modules.py`
5. Add tests in `tests/unit/agents/test_modules.py`

## Adding a New Pipeline Node

1. Create a node function in `app/graph/nodes/`
2. Accept `PRReviewState`, return a partial state dict
3. Register in `app/graph/builder.py` with `graph.add_node()`
4. Add edges/conditional edges as needed
5. Add tests in `tests/unit/graph/test_builder.py`
