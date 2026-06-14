# Mocking Guidelines (Prism)

## When to Mock

### External Services (Always Mock)

These are I/O boundaries that make tests slow, flaky, or expensive.

| What | Why Mock | How |
|------|----------|-----|
| `ChatOpenAI` | LLM calls cost money, take seconds | `MagicMock(return_value=mock_response)` |
| `httpx` (GitHub API) | Network calls, rate limits | `pytest-httpx` or `respx` |
| `PGVectorStore` | Requires PostgreSQL | Mock the `RAGStore` protocol |
| `asyncio.to_thread` | Thread pool overhead | Mock the wrapped function |

```python
# Mocking LLM calls
def test_security_agent_uses_llm():
    agent = SecurityAgent()
    mock_result = MagicMock()
    mock_result.findings = '[{"finding": "x"}]'
    mock_result.rationale = "reasoning"
    agent.review = MagicMock(return_value=mock_result)

    result = agent(files_changed="x.py", diff="+y")
    assert result["findings"] == [{"finding": "x"}]
```

### Internal Logic (Never Mock)

These are pure functions or simple logic that should be tested directly.

| What | Why Not Mock | Test Instead |
|------|--------------|--------------|
| `parse_findings()` | Pure function, no side effects | Call directly, verify output |
| `weighted_score()` | Domain logic, core behavior | Call directly, verify math |
| `_finding_matches()` | Matching logic, testable | Call directly, verify boolean |
| Pydantic models | Data validation, testable | Create instances, verify fields |

```python
# Testing pure function directly
def test_parse_findings_handles_json_string():
    result = parse_findings('[{"finding": "x"}]')
    assert result == [{"finding": "x"}]

def test_parse_findings_handles_list_passthrough():
    data = [{"finding": "x"}]
    result = parse_findings(data)
    assert result is data  # same object, not copied
```

---

## Prism-Specific Patterns

### Mocking Agent Results

```python
# Pattern: Mock agent forward() to return controlled results
mock_result = {
    "agent_name": "security",
    "findings": [
        {"finding": "SQL injection", "severity": "critical", "confidence": 0.9}
    ],
    "reasoning": "Found SQL injection risk"
}
agent.forward = MagicMock(return_value=mock_result)
```

### Mocking Pipeline Stages

```python
# Pattern: Mock FullReviewPipeline for integration tests
pipeline = FullReviewPipeline()
pipeline.orchestrator = MagicMock(return_value={
    "security": {"findings": []},
    "performance": {"findings": []},
})
pipeline.debate = MagicMock(return_value={
    "debate_records": [],
    "agent_results": {"security": {"findings": []}},
})
pipeline.judge = MagicMock(return_value={
    "summary": "OK",
    "approved": True,
})
```

### Mocking for Async Code

```python
# Pattern: Mock asyncio.to_thread for sync pipeline in async node
with patch("asyncio.to_thread", return_value=mock_verdict):
    result = await review_node(state)
```

---

## Anti-Patterns to Avoid

### Don't Mock What You Don't Own

```python
# BAD: Mocking internal Python behavior
with patch("json.loads", return_value=[]):
    parse_findings("[]")

# GOOD: Let json.loads work, test parse_findings behavior
result = parse_findings("[]")
assert result == []
```

### Don't Over-Mock

```python
# BAD: Mocking everything makes test meaningless
with patch("app.agents.security.SecurityAgent.review"):
    with patch("app.agents.performance.PerformanceAgent.review"):
        with patch("app.agents.maintainability.MaintainabilityAgent.review"):
            # ... test is now testing mocks, not code

# GOOD: Mock only external boundaries
agent = SecurityAgent()
agent.review = MagicMock(return_value=mock_result)  # mock LLM only
result = agent(files_changed="x.py", diff="+y")
```

### Don't Verify Implementation Details

```python
# BAD: Verifying internal call order
orch = ReviewOrchestrator()
orch(files_changed="x.py", diff="+y")
orch.agents["security"].forward.assert_called_before(
    orch.agents["performance"].forward
)

# GOOD: Verify output is correct
result = orch(files_changed="x.py", diff="+y")
assert "security" in result
assert "performance" in result
```
