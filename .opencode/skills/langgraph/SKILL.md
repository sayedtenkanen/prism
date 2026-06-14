---
name: langgraph
description: LangGraph state, nodes, edges, and graph construction. Use when user mentions "langgraph", "graph", "node", "edge", "state". Triggers on LangGraph questions.
---

# LangGraph Conventions

## State

```python
from typing import Any, Optional
from typing_extensions import TypedDict

class PRReviewState(TypedDict, total=False):
    # Input
    owner: str
    repo: str
    pr_number: int
    scm_token: str
    scm_provider: str
    hitl_enabled: bool

    # LLM Config
    llm_model: str
    llm_api_key: str

    # Fetched PR Data
    pr_metadata: Optional[dict[str, Any]]
    diff: Optional[str]
    files_changed: Optional[str]

    # Detection
    languages: list[str]

    # DSPy Review Results
    agent_results: Optional[dict[str, Any]]
    debate_records: list[dict[str, Any]]

    # Judge Verdict
    summary: Optional[str]
    critical_findings: list[dict[str, Any]]
    major_findings: list[dict[str, Any]]
    minor_findings: list[dict[str, Any]]
    approved: bool

    # Output
    review_url: Optional[str]
    json_report_path: Optional[str]

    # Error tracking
    errors: list[str]
    retry_counts: dict[str, int]
```

## Nodes

```python
# All nodes are async
async def fetch_pr(state: PRReviewState) -> dict[str, Any]:
    # Fetch PR data from GitHub
    return {"pr_metadata": metadata, "diff": diff, "files_changed": files}

async def detect_node(state: PRReviewState) -> dict[str, Any]:
    # Detect languages from filenames
    return {"languages": languages}

async def review_node(state: PRReviewState) -> dict[str, Any]:
    # Run DSPy FullReviewPipeline
    return {"agent_results": results, "critical_findings": critical}

async def output_node(state: PRReviewState) -> PRReviewState:
    # Generate JSON report and optional PR comment
    return state
```

## Graph Construction

```python
from langgraph.graph import StateGraph, END

def build_graph():
    graph = StateGraph(PRReviewState)

    graph.add_node("fetch_pr", fetch_pr)
    graph.add_node("detect_languages", detect_node)
    graph.add_node("run_review", review_node)
    graph.add_node("human_approval", human_approval)
    graph.add_node("output", output_node)

    graph.set_entry_point("fetch_pr")
    graph.add_edge("fetch_pr", "detect_languages")
    graph.add_edge("detect_languages", "run_review")
    graph.add_conditional_edges("run_review", should_continue, {"output": "output", "human_approval": "human_approval"})
    graph.add_edge("human_approval", "output")
    graph.add_edge("output", END)

    return graph.compile()
```

## Edges

```python
# Simple edge
graph.add_edge("node_a", "node_b")

# Conditional edge
def should_continue(state: PRReviewState) -> str:
    if state.get("errors"):
        return "output"
    if state.get("hitl_enabled"):
        return "human_approval"
    return "output"

graph.add_conditional_edges("run_review", should_continue, {"output": "output", "human_approval": "human_approval"})

# Entry/exit
graph.set_entry_point("fetch_pr")
graph.add_edge("output", END)
```

## Pipeline Flow

```
fetch_pr → detect_languages → run_review → [human_approval] → output → END
```

## Key Patterns

- Nodes are async functions
- State is TypedDict with `total=False`
- Nodes return partial state updates
- Conditional edges for branching (HITL, error handling)
- Use `asyncio.to_thread` for sync code (e.g., FullReviewPipeline)
- `get_graph()` returns singleton graph instance

## Checklist

Before writing LangGraph code:

```bash
ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```
