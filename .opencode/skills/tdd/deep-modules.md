# Deep Module Patterns (Prism)

## What is a Deep Module?

A deep module has a **small public interface** but **deep implementation**. The complexity is hidden behind simple functions/classes. Users don't need to understand the internals.

**Shallow module**: Many methods, complex interface, little implementation.
**Deep module**: Few methods, simple interface, substantial implementation.

---

## Prism Deep Modules

### BaseAgent

```
Public interface:
  - forward(files_changed: str, diff: str) -> dict

Hidden complexity:
  - LLM prompt construction
  - Response parsing (JSON extraction)
  - Error handling for invalid responses
  - Finding normalization
```

**Why it's deep**: Users call `agent(files_changed, diff)` and get structured findings. They don't need to know about `dspy.ChainOfThought`, JSON parsing, or error recovery.

```python
# Good: Test through public interface
def test_security_agent_forward():
    agent = SecurityAgent()
    # ... mock LLM ...
    result = agent(files_changed="x.py", diff="+y")
    assert "findings" in result

# Bad: Test internal implementation
def test_security_agent_prompt_construction():
    agent = SecurityAgent()
    prompt = agent._build_prompt("x.py", "+y")  # private method
    assert "Security" in prompt
```

### ReviewOrchestrator

```
Public interface:
  - forward(files_changed: str, diff: str) -> dict[str, Any]

Hidden complexity:
  - Running 6 agents sequentially
  - Collecting results from each
  - Error handling per agent
  - Result aggregation
```

**Why it's deep**: Users call `orchestrator(files_changed, diff)` and get all agent results. They don't need to know about agent ordering, parallelism, or error recovery.

### FullReviewPipeline

```
Public interface:
  - forward(files_changed: str, diff: str) -> dict[str, Any]

Hidden complexity:
  - Orchestrator running all agents
  - Debate module cross-challenging findings
  - Judge module aggregating into verdict
  - Confidence thresholding
  - Domain weight application
```

**Why it's deep**: Users call `pipeline(files_changed, diff)` and get a final verdict. The entire review process is hidden behind one call.

### RAGStore Protocol

```
Public interface:
  - add(id, embedding, metadata)
  - search(query_embedding, top_k)
  - delete(id)
  - count()

Hidden complexity:
  - PGVector connection management
  - Async client initialization
  - Vector similarity search
  - Connection pooling
  - Timeout handling
```

**Why it's deep**: Implementations hide database complexity behind simple CRUD operations.

---

## Designing Deep Modules

### Rule of thumb

If a module has more than 5 public methods, it's probably too shallow. Consider:

1. **Extract internal logic** into private methods
2. **Combine related operations** into higher-level methods
3. **Use protocols** to define clean interfaces

### Prism Example: DebateModule

**Shallow version** (bad):
```python
class DebateModule:
    def get_challenges(self, agent_name): ...
    def should_challenge(self, finding): ...
    def calculate_adjustment(self, finding, challenge): ...
    def apply_adjustment(self, finding, adjustment): ...
    def build_record(self, finding, challenge, adjustment): ...
```

**Deep version** (good):
```python
class DebateModule:
    def forward(self, agent_results: dict, diff: str) -> dict:
        # All logic hidden inside forward()
        # Users call debate(agent_results, diff)
        # They don't need to know about challenge calculation,
        # adjustment application, or record building
```

---

## Testing Deep Modules

### Test the interface, not the implementation

```python
# GOOD: Test what FullReviewPipeline does
def test_full_pipeline_returns_approved():
    pipeline = FullReviewPipeline()
    # ... mock agents ...
    result = pipeline(files_changed="x.py", diff="+y")
    assert result["approved"] is True

# BAD: Test how FullReviewPipeline does it
def test_full_pipeline_calls_orchestrator_then_debate_then_judge():
    pipeline = FullReviewPipeline()
    pipeline.orchestrator = MagicMock()
    pipeline.debate = MagicMock()
    pipeline.judge = MagicMock()
    pipeline(files_changed="x.py", diff="+y")
    pipeline.orchestrator.assert_called_once()  # testing implementation
```

### Test edge cases at the interface

```python
def test_pipeline_handles_empty_diff():
    pipeline = FullReviewPipeline()
    result = pipeline(files_changed="x.py", diff="")
    assert "summary" in result

def test_pipeline_handles_no_findings():
    pipeline = FullReviewPipeline()
    # ... mock agents to return no findings ...
    result = pipeline(files_changed="x.py", diff="+y")
    assert result["approved"] is True  # no findings = approved
```
