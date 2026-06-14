# Prism

Pull Request Inspection, Synthesis & Monitoring — an AI-powered multi-language PR review tool with self-improving agent capabilities using DSPy and LangGraph.

## Features

- **DSPy-powered agents**: 6 specialized review agents (Security, Performance, Maintainability, Testing, Architecture, Documentation) with ChainOfThought reasoning
- **Multi-agent debate**: Agents challenge each other's findings with evidence-based reasoning
- **Confidence tracking**: Domain-weighted scoring with per-agent expertise weights
- **AI Judge**: Aggregates and deduplicates findings into a single verdict
- **LangGraph pipeline**: `fetch_pr → detect → review → debate → judge → output`
- **SIA (Self-Improving Agent)**: Feedback loops that collect reviewer actions, build training datasets, and optimize agent prompts via DSPy optimizers
- **RAG layer**: Store and retrieve past review findings for context
- **Human-in-the-loop**: Approval gate before posting results
- **GitHub integration**: Fetches PRs, posts summary comments, stores JSON reports
- **Multi-language**: Python, Java, C++, Ada, Markdown
- **Test integration**: pytest/Maven/CTest with per-language coverage thresholds

## Quick Start

### Prerequisites

- Python 3.12+
- GitHub token (with repo access)
- OpenAI API key (or compatible provider)

### Installation

```bash
git clone https://github.com/sayedtenkanen/prism.git
cd prism
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Configuration

```bash
# LLM
export LLM_API_KEY="your-openai-api-key"
export LLM_PROVIDER="openai"

# GitHub
export SCM_GITHUB_TOKEN="your-github-token"
```

Or create a `.env` file:

```env
LLM_API_KEY=your-openai-api-key
SCM_GITHUB_TOKEN=your-github-token
```

### Running

```bash
# Run the graph pipeline
python -c "
from app.graph.builder import get_graph
from app.graph.state import create_initial_state
import asyncio

state = create_initial_state(owner='octocat', repo='hello-world', pr_number=1, scm_token='...')
graph = get_graph()
result = asyncio.run(graph.ainvoke(state))
print(result['summary'])
"
```

## Architecture

```
PR Input
    │
    ▼
┌─────────────┐
│  fetch_pr   │  GitHub API → metadata, diff, files
└─────────────┘
    │
    ▼
┌──────────────┐
│ detect_languages │  Language detection from filenames
└──────────────┘
    │
    ▼
┌──────────────┐
│  run_review  │  DSPy FullReviewPipeline
│              │  ├─ 6 agents (parallel review)
│              │  ├─ DebateModule (cross-challenge)
│              │  └─ JudgeModule (aggregation)
└──────────────┘
    │
    ▼
┌──────────────┐
│ [human_approval] │  Optional HITL gate
└──────────────┘
    │
    ▼
┌─────────────┐
│   output    │  JSON report + optional PR comment
└─────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                SIA Feedback Loop                    │
│  memory_store ← findings                           │
│  feedback ← reviewer_actions (accept/reject/modify)│
│  dataset_builder → training_data                   │
│  dspy_optimizer ← training_data                    │
└─────────────────────────────────────────────────────┘
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `app/agents/signatures.py` | DSPy Signatures (input/output specs for LLM reasoning) |
| `app/agents/base.py` | `BaseAgent` with shared `parse_findings` helper |
| `app/agents/{security,performance,...}.py` | 6 specialized review agents |
| `app/agents/modules.py` | `ReviewOrchestrator`, `DebateModule`, `JudgeModule`, `FullReviewPipeline` |
| `app/graph/builder.py` | LangGraph pipeline wiring |
| `app/graph/nodes/` | Pipeline node implementations |
| `app/rag/` | RAG store interface + PGVector implementation |
| `app/scm/` | SCM client protocol + GitHub implementation |
| `app/core/config.py` | Pydantic settings (LLM, DSPy, SCM, Test, Storage) |
| `app/sia/memory.py` | `MemoryStore` — persistent review history with search |
| `app/sia/feedback.py` | `FeedbackCollector` — reviewer actions (accept/reject/modify) |
| `app/sia/dataset.py` | `DatasetBuilder` — training data from memory + feedback |
| `app/eval/optimizer.py` | `ReviewOptimizer` — DSPy BootstrapFewShot/LabeledFewShot |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | OpenAI API key |
| `LLM_PROVIDER` | `openai` | LLM provider |
| `LLM_PYTHON_REVIEWER_MODEL` | `gpt-4o` | Model for Python review |
| `LLM_JUDGE_MODEL` | `gpt-4o` | Model for judge aggregation |
| `LLM_TEMPERATURE` | `0.3` | LLM temperature |
| `SCM_PROVIDER` | `github` | SCM provider |
| `SCM_GITHUB_TOKEN` | — | GitHub personal access token |
| `DSPY_OPTIMIZER` | `bootstrapFewShot` | DSPy optimizer algorithm |
| `PRISM_HITL_ENABLED` | `true` | Enable human-in-the-loop |
| `PRISM_RETRY_MAX_ATTEMPTS` | `3` | Max retries per node |
| `PRISM_LOG_LEVEL` | `INFO` | Log level |
| `STORAGE_DB_PATH` | `prism.db` | SQLite database path |
| `STORAGE_JSON_STORAGE_PATH` | `./reports` | JSON report output directory |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run checks
ruff check .
ruff format --check .
mypy app/
pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```

## Tech Stack

- **Python 3.12** — runtime
- **DSPy 3.2** — LLM program framework (Signatures, Modules, ChainOfThought)
- **LangGraph** — workflow orchestration and state management
- **Pydantic v2** — settings and data validation
- **FastAPI + Uvicorn** — API server
- **Ruff** — linting and formatting (line-length 120)
- **Mypy** — static type checking
- **Pytest + Coverage** — testing (90% threshold)
- **GitHub Actions** — CI/CD
- **CodeQL** — code scanning
- **Docker** — multi-stage build

## License

MIT
