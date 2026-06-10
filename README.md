# Prism

Pull Request Inspection, Synthesis & Monitoring — an AI-powered multi-language PR review tool.

## Features

- **Multi-language support**: Python, Java, C++, Ada, Markdown
- **Parallel reviewers**: Language-specific reviewers run concurrently via LangGraph Send API
- **Configurable LLM models**: Different models per reviewer node
- **Test integration**: Runs pytest/Maven/CTest, enforces per-language coverage thresholds
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

See [PLAN.md](PLAN.md) for full architecture details, pipeline nodes, and configuration reference.

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
