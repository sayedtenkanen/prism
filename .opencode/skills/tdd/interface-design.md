# Interface Design for Testability (Prism)

## Core Principle

Design interfaces that make testing easy. If testing is hard, the interface is wrong.

---

## Patterns for Testability

### 1. Protocols for External Dependencies

Use `typing.Protocol` to define interfaces for external services. This allows mocking at the boundary.

```python
# app/scm/client.py
from typing import Protocol

class SCMClient(Protocol):
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict: ...
    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]: ...
    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str: ...

# Implementation
class GitHubClient:
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        # Real GitHub API call
        ...

# Test double
class MockGitHubClient:
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        return {"title": "Test PR", "state": "open"}
```

**Why it works**: Tests use `MockGitHubClient`, production uses `GitHubClient`. Both satisfy `SCMClient` protocol.

### 2. Dependency Injection via Constructor

Pass dependencies through `__init__`, don't create them inside methods.

```python
# GOOD: Injectable
class ReviewNode:
    def __init__(self, pipeline: FullReviewPipeline | None = None):
        self.pipeline = pipeline or get_pipeline()

# BAD: Hard-coded dependency
class ReviewNode:
    def __init__(self):
        self.pipeline = FullReviewPipeline()  # can't mock in tests
```

### 3. Async Nodes with Sync Internals

Prism uses `asyncio.to_thread` to run sync DSPy pipelines in async LangGraph nodes.

```python
# app/graph/nodes/review_node.py
async def review_node(state: PRReviewState) -> dict[str, Any]:
    pipeline = get_pipeline()
    # Run sync pipeline in thread pool
    result = await asyncio.to_thread(
        pipeline,
        files_changed=state["files_changed"],
        diff=state["diff"],
    )
    return result
```

**Why it works**: Tests can mock `get_pipeline()` without dealing with async complexity.

### 4. Pydantic Models for Type-Safe State

LangGraph state is a TypedDict with Pydantic models for validation.

```python
from typing import TypedDict
from pydantic import BaseModel

class PRReviewState(TypedDict, total=False):
    owner: str
    repo: str
    pr_number: int
    files_changed: str
    diff: str
    languages: list[str]
    approved: bool
    # ...
```

**Why it works**: Tests can create state dicts directly, no complex setup needed.

---

## Prism Interface Patterns

### Agent Interface

All agents follow the same pattern:

```python
class BaseAgent(dspy.Module):
    agent_name: str
    review: dspy.ChainOfThought

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        return {
            "agent_name": self.agent_name,
            "findings": parse_findings(result.findings),
            "reasoning": result.rationale,
        }
```

**Testability**: Tests mock `self.review` and verify output structure.

### RAG Store Interface

Abstract base with concrete implementations:

```python
class RAGStore(Protocol):
    async def add(self, id: str, embedding: list[float], metadata: dict) -> None: ...
    async def search(self, query_embedding: list[float], top_k: int) -> list[dict]: ...
    async def delete(self, id: str) -> None: ...
    async def count(self) -> int: ...

class PGVectorStore:
    # Real implementation with PostgreSQL
    ...

class MockRAGStore:
    # In-memory test double
    ...
```

**Testability**: Tests use `MockRAGStore`, production uses `PGVectorStore`.

---

## Testing Interface Contracts

### Verify Protocol Compliance

```python
def test_github_client_satisfies_protocol():
    client = GitHubClient(token="...")
    assert hasattr(client, "get_pr")
    assert hasattr(client, "get_pr_files")
    assert hasattr(client, "get_pr_diff")
```

### Test Interface Invariants

```python
def test_scm_client_get_pr_returns_dict():
    client = MockGitHubClient()
    result = asyncio.run(client.get_pr("org", "repo", 1))
    assert isinstance(result, dict)
    assert "title" in result
```

### Test Error Handling at Boundaries

```python
def test_scm_client_handles_not_found():
    client = MockGitHubClient()
    client.get_pr = MagicMock(side_effect=HTTPError(404))
    with pytest.raises(HTTPError):
        asyncio.run(client.get_pr("org", "repo", 999))
```

---

## Common Anti-Patterns

### Don't Create Dependencies Inside Methods

```python
# BAD
def review_code(files_changed: str, diff: str) -> dict:
    llm = ChatOpenAI(model="gpt-4o")  # can't mock
    return llm.invoke(...)

# GOOD
def review_code(files_changed: str, diff: str, llm: ChatOpenAI | None = None) -> dict:
    llm = llm or ChatOpenAI(model="gpt-4o")
    return llm.invoke(...)
```

### Don't Use Global State for Dependencies

```python
# BAD
_pipeline = FullReviewPipeline()  # global, hard to override in tests

def review(state):
    return _pipeline(files_changed=state["files_changed"], diff=state["diff"])

# GOOD
_pipeline: FullReviewPipeline | None = None

def get_pipeline() -> FullReviewPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FullReviewPipeline()
    return _pipeline

def review(state, pipeline: FullReviewPipeline | None = None):
    pipe = pipeline or get_pipeline()
    return pipe(files_changed=state["files_changed"], diff=state["diff"])
```

### Don't Mix I/O with Logic

```python
# BAD
def process_pr(owner: str, repo: str, pr_number: int) -> dict:
    # I/O and logic mixed
    files = github.get_pr_files(owner, repo, pr_number)
    findings = []
    for file in files:
        if file["filename"].endswith(".py"):
            findings.append(analyze_python(file))
    return {"findings": findings}

# GOOD: Separate I/O from logic
def process_pr_files(files: list[dict]) -> dict:
    # Pure logic, easy to test
    findings = []
    for file in files:
        if file["filename"].endswith(".py"):
            findings.append(analyze_python(file))
    return {"findings": findings}

async def process_pr(owner: str, repo: str, pr_number: int) -> dict:
    # I/O at the boundary
    files = await github.get_pr_files(owner, repo, pr_number)
    return process_pr_files(files)
```
