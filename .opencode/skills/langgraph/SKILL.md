---
name: langgraph
description: LangGraph state, nodes, edges, and graph construction. Use when user mentions "langgraph", "graph", "node", "edge", "state". Triggers on LangGraph questions.
---

# LangGraph Conventions

## State

```python
from typing import TypedDict, Any

class ReviewState(TypedDict):
    pr_number: int
    repo: str
    findings: list[dict[str, Any]]
    verdict: str
```

## Nodes

```python
# All nodes are async
async def fetch_pr(state: ReviewState) -> dict[str, Any]:
    # Fetch PR data
    return {"findings": findings}

async def review_code(state: ReviewState) -> dict[str, Any]:
    # Run review pipeline
    return {"verdict": verdict}
```

## Graph Construction

```python
from langgraph.graph import StateGraph, END

def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("fetch_pr", fetch_pr)
    graph.add_node("review", review_code)
    graph.add_edge("fetch_pr", "review")
    graph.add_edge("review", END)
    graph.set_entry_point("fetch_pr")
    return graph.compile()
```

## Edges

```python
# Simple edge
graph.add_edge("node_a", "node_b")

# Conditional edge
def should_continue(state: ReviewState) -> str:
    if state.get("errors"):
        return "error_handler"
    return "review"

graph.add_conditional_edges("fetch_pr", should_continue)

# Entry/exit
graph.set_entry_point("fetch_pr")
graph.add_edge("review", END)
```

## Key Patterns

- Nodes are async functions
- State is TypedDict
- Nodes return partial state updates
- Conditional edges for branching
- Use `asyncio.to_thread` for sync code

## Checklist

Before writing LangGraph code:

```bash
mypy app/
```
