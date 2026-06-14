# Prism — DSPy Rewrite Plan

## Architecture

LangGraph orchestrates a DSPy-powered review pipeline:

```
fetch_pr → detect_languages → [review agents] → debate → judge → output
```

Each review agent is a `dspy.Module` with a `dspy.ChainOfThought` signature. A `DebateModule` cross-challenges findings. A `JudgeModule` aggregates into a deduplicated verdict.

## Phases

### Completed

- [x] Phase 1: DSPy foundation — signatures, SCM protocol, Python 3.12 upgrade
- [x] Phase 2: 6 agent modules + orchestrator + judge
- [x] Phase 3: Judge + debate + confidence tracking (domain weights)
- [x] Phase 4: LangGraph graph state rewrite + builder + pipeline nodes
- [x] Phase 5: RAG layer — abstract store, PGVector, retriever

### Remaining

- [ ] Phase 6: Evaluation framework — metrics, benchmarks, DSPy optimizer integration
- [ ] Phase 7: Observability — traces, cost tracking, latency
- [ ] Phase 8: SIA-ready interfaces — memory store, feedback collector, dataset builder
- [ ] Phase 9: CLI (Click) + Daemon (FastAPI + APScheduler)
- [ ] Phase 10: CI/CD update — PostgreSQL+pgvector docker-compose, E2E tests

## Tech Stack

- Python 3.12, DSPy 3.2, LangGraph, Pydantic v2
- Ruff (lint + format), Mypy, Pytest (90% coverage)
- GitHub Actions, CodeQL, Docker multi-stage

## Key Design Decisions

- **Hybrid LangGraph + DSPy**: LangGraph for workflow/state/retry/HITL, DSPy for review Signatures/Modules/optimization
- **BaseAgent**: Shared `forward` + `parse_findings` — no duplicated parsing
- **Domain weights**: Security 1.0, Architecture 0.9, Performance/Testing 0.8, Maintainability 0.7, Documentation 0.5
- **Debate threshold**: Findings with confidence ≥ 0.5 are challenged by cross-domain agents
- **SCMProvider enum**: Type-safe provider selection with runtime assertion in `fetch_pr`
- **PGVectorStore**: Eagerly initialized `AsyncClient` for concurrency safety
