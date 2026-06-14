# When to Mock

Mock at **system boundaries** only:

- External APIs (payment, email, etc.)
- Databases (sometimes - prefer test DB)
- Time/randomness
- File system (sometimes)

Don't mock:

- Your own classes/modules
- Internal collaborators
- Anything you control

## Designing for Mockability

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in rather than creating them internally:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create specific functions for each external operation instead of one generic function with conditional logic:

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint

---

## Prism Examples

### Mocking Agent Results

```python
# Pattern: Mock agent forward() to return controlled results
agent = SecurityAgent()
mock_result = {
    "agent_name": "security",
    "findings": [{"finding": "SQL injection", "severity": "critical", "confidence": 0.9}],
    "reasoning": "Found SQL injection risk"
}
agent.review = MagicMock(return_value=mock_result)

result = agent(files_changed="app.py", diff="+cursor.execute(query)")
assert result["findings"][0]["severity"] == "critical"
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

result = pipeline(files_changed="x.py", diff="+y")
assert result["approved"] is True
```

### Mocking External LLM Calls

```python
# Pattern: Mock ChatOpenAI for LLM-dependent tests
def test_security_agent_uses_llm():
    agent = SecurityAgent()
    mock_result = MagicMock()
    mock_result.findings = '[{"finding": "x"}]'
    mock_result.rationale = "reasoning"
    agent.review = MagicMock(return_value=mock_result)

    result = agent(files_changed="x.py", diff="+y")
    assert result["findings"] == [{"finding": "x"}]
```

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
