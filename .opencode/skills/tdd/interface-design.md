# Interface Design for Testability

Good interfaces make testing natural:

1. **Accept dependencies, don't create them**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, don't produce side effects**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area**
   - Fewer methods = fewer tests needed
   - Fewer params = simpler test setup

---

## Prism Examples

### Protocols for External Dependencies

```python
# app/scm/client.py
from typing import Protocol

class SCMClient(Protocol):
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict: ...
    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]: ...

# Test double
class MockGitHubClient:
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        return {"title": "Test PR", "state": "open"}
```

### Dependency Injection via Constructor

```python
# GOOD: Injectable
class ReviewNode:
    def __init__(self, pipeline: FullReviewPipeline | None = None):
        self.pipeline = pipeline or get_pipeline()

# BAD: Hard-coded dependency
class ReviewNode:
    def __init__(self):
        self.pipeline = FullReviewPipeline()  # can't mock
```

### Async Nodes with Sync Internals

```python
async def review_node(state: PRReviewState) -> dict[str, Any]:
    pipeline = get_pipeline()
    result = await asyncio.to_thread(
        pipeline,
        files_changed=state["files_changed"],
        diff=state["diff"],
    )
    return result
```

### Pydantic Models for Type-Safe State

```python
class PRReviewState(TypedDict, total=False):
    owner: str
    repo: str
    pr_number: int
    files_changed: str
    diff: str
    languages: list[str]
    approved: bool
```

### Agent Interface

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

### RAG Store Protocol

```python
class RAGStore(Protocol):
    async def add(self, id: str, embedding: list[float], metadata: dict) -> None: ...
    async def search(self, query_embedding: list[float], top_k: int) -> list[dict]: ...
    async def delete(self, id: str) -> None: ...
    async def count(self) -> int: ...
```
