# PRism

Pull Request Inspection, Synthesis & Monitoring — an AI-powered multi-language PR review tool.

## Features

- **Multi-language support**: Python, Java, C++, Ada, Markdown
- **Parallel reviewers**: Language-specific reviewers run concurrently via LangGraph Send API
- **Configurable LLM models**: Different models per reviewer node
- **Test integration**: Runs pytest/maven/ctest, enforces per-language coverage thresholds
- **AI Judge**: Deduplicates and summarizes all reviewer outputs into a single verdict
- **Human-in-the-loop**: Approval gate before posting results to Bitbucket
- **Bitbucket integration**: Fetches PRs, posts summary comments, stores JSON artifacts
- **CodeQL scanning**: Automated security analysis in CI

## Quick Start

### Prerequisites

- Python 3.9+
- Bitbucket Server (on-prem) access
- OpenAI API key (or compatible provider)

### Installation

```bash
git clone https://github.com/sayedtenkanen/prism.git
cd prism
pip install -e ".[dev]"
```

### Configuration

Set environment variables:

```bash
# LLM
export LLM_API_KEY="your-openai-api-key"
export LLM_PROVIDER="openai"
export LLM_PYTHON_REVIEWER_MODEL="gpt-4o"

# Bitbucket
export BB_URL="https://bitbucket.example.com"
export BB_TOKEN="your-bitbucket-token"
```

Or create a `.env` file:

```env
LLM_API_KEY=your-openai-api-key
BB_URL=https://bitbucket.example.com
BB_TOKEN=your-bitbucket-token
```

### Running

```bash
# Run full pipeline
python -m app.cli review --project KEY --repo slug --pr 123

# Start daemon mode
python -m app.daemon
```

## Architecture

```
fetch_pr → detect_languages → [parallel reviewers] → test_executor → aggregate → compare → HITL → output → storage
                                    ├── python
                                    ├── java
                                    ├── cpp
                                    ├── ada
                                    └── docs
```

### Pipeline Nodes

| Node | Description |
|------|-------------|
| `fetch_pr` | Fetch PR metadata, diff, and file list from Bitbucket |
| `detect_languages` | Identify languages from file extensions |
| `reviewers` | Language-specific LLM-powered code review |
| `test_executor` | Run test suites, parse results, enforce coverage thresholds |
| `aggregate` | AI Judge deduplicates and summarizes all reviewer outputs |
| `compare` | Diff current review against previous review |
| `human_approval` | LangGraph interrupt for human approval gate |
| `output` | Format and post summary comment to Bitbucket |
| `storage` | Persist results to SQLite + JSON files |

## Configuration Reference

### LLM Config

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider |
| `LLM_JUDGE_MODEL` | `gpt-4o` | Model for AI Judge |
| `LLM_PYTHON_REVIEWER_MODEL` | `gpt-4o` | Model for Python reviewer |
| `LLM_JAVA_REVIEWER_MODEL` | `gpt-4o` | Model for Java reviewer |
| `LLM_CPP_REVIEWER_MODEL` | `gpt-4o` | Model for C++ reviewer |
| `LLM_ADA_REVIEWER_MODEL` | `gpt-4o` | Model for Ada reviewer |
| `LLM_DOCS_REVIEWER_MODEL` | `gpt-4o` | Model for Docs reviewer |
| `LLM_TEMPERATURE` | `0.3` | LLM temperature |

### Bitbucket Config

| Setting | Default | Description |
|---------|---------|-------------|
| `BB_URL` | `https://bitbucket.example.com` | Bitbucket Server URL |
| `BB_TOKEN` | — | Bitbucket API token |

### Test Config

| Setting | Default | Description |
|---------|---------|-------------|
| `TEST_COVERAGE_THRESHOLD` | `80.0` | Default coverage threshold |
| `TEST_FAIL_ON_COVERAGE_BELOW` | `true` | Fail pipeline if coverage below threshold |
| `TEST_FAIL_ON_TEST_FAILURE` | `true` | Fail pipeline if tests fail |
| `TEST_TEST_TIMEOUT` | `300` | Test execution timeout (seconds) |

Per-language thresholds:

| Language | Default |
|----------|---------|
| Python | 85.0% |
| Java | 80.0% |
| C++ | 75.0% |
| Ada | 70.0% |

Per-project thresholds can override language defaults via `TEST_PROJECT_THRESHOLD_<project_key>`.

## Development

### Setup

```bash
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest
pytest --cov=app --cov-report=html
```

### Linting

```bash
ruff check .
ruff format --check .
mypy app/
```

### CI/CD

GitHub Actions runs on push to `main`/`develop` and PRs:
- Ruff lint + format check
- Mypy type checking
- Pytest with 90% coverage threshold
- CodeQL security scanning
- Docker build + health check

## License

MIT
