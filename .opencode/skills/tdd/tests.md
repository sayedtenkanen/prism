# Good and Bad Tests

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

Characteristics:

- Tests behavior users/callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts/order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying through external means instead of interface

```typescript
// BAD: Bypasses interface to verify
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: Verifies through interface
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

---

## Prism Examples

### Good: Testing Through Public Interface

```python
class TestSecurityAgent:
    def test_forward_returns_findings(self):
        agent = SecurityAgent()
        mock_result = MagicMock()
        mock_result.findings = '[{"finding": "SQL injection", "severity": "critical", "confidence": 0.9}]'
        mock_result.rationale = "Found SQL injection risk"
        agent.review = MagicMock(return_value=mock_result)

        result = agent(files_changed="app.py", diff="+cursor.execute(query)")

        assert result["agent_name"] == "security"
        assert len(result["findings"]) == 1
        assert result["findings"][0]["severity"] == "critical"
```

**Why it's good**: Tests the public `forward()` interface. Doesn't care how `review` is implemented internally.

### Good: Testing Domain Logic

```python
class TestWeightedScore:
    def test_security_finding_has_full_weight(self):
        finding = {"confidence": 0.8}
        result = weighted_score(finding, "security")
        assert result == 0.8  # security weight = 1.0

    def test_documentary_finding_has_half_weight(self):
        finding = {"confidence": 0.8}
        result = weighted_score(finding, "documentation")
        assert result == 0.4  # documentation weight = 0.5
```

**Why it's good**: Tests the domain logic directly. Clear relationship between input and expected output.

### Bad: Testing Private Methods

```python
class TestSecurityAgent:
    def test_build_prompt_format(self):
        agent = SecurityAgent()
        prompt = agent._build_prompt("app.py", "+line")
        assert "Security Review" in prompt
        assert "app.py" in prompt
```

**Why it's bad**: Tests `_build_prompt()` private method. If you rename it or extract it, test breaks but behavior is unchanged.

### Bad: Testing Internal Call Order

```python
class TestReviewOrchestrator:
    def test_orchestrator_calls_internal_agents(self):
        orch = ReviewOrchestrator()
        orch.agents["security"] = MagicMock()
        orch.agents["performance"] = MagicMock()

        orch(files_changed="x.py", diff="+y")

        orch.agents["security"].forward.assert_called_once()
        orch.agents["performance"].forward.assert_called_once()
```

**Why it's bad**: Tests implementation detail (which internal agents are called). If you change agent ordering or add parallelism, test breaks.
