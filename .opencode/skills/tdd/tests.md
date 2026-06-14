# Test Examples (Prism)

## Good Tests (Behavior-Focused)

These tests verify _what_ the system does through public interfaces.

### TestSecurityAgent

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

### TestWeightedScore

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

### TestDebateModule

```python
class TestDebateModule:
    def test_challenge_reduces_confidence(self):
        debate = DebateModule()
        mock_result = MagicMock()
        mock_result.challenge = "Invalid finding"
        mock_result.confidence_adjustment = -0.5
        debate.challenge = MagicMock(return_value=mock_result)

        agent_results = {
            "security": {"findings": [{"finding": "x", "confidence": 0.8}]},
        }
        result = debate(agent_results=agent_results, diff="+y")

        assert len(result["debate_records"]) == 1
        assert result["debate_records"][0]["new_confidence"] == pytest.approx(0.3)
```

**Why it's good**: Integration test that exercises the debate flow through public interface.

---

## Bad Tests (Implementation-Coupled)

These tests break when you refactor, even if behavior hasn't changed.

### BAD: Testing Private Methods

```python
class TestSecurityAgent:
    def test_build_prompt_format(self):
        agent = SecurityAgent()
        prompt = agent._build_prompt("app.py", "+line")
        assert "Security Review" in prompt
        assert "app.py" in prompt
```

**Why it's bad**: Tests `_build_prompt()` private method. If you rename it or extract it, test breaks but behavior is unchanged.

### BAD: Mocking Internal Collaborators

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

### BAD: Testing Data Structure Shape

```python
class TestAgentReview:
    def test_agent_review_has_required_fields(self):
        review = AgentReview(agent_name="security")
        assert hasattr(review, "agent_name")
        assert hasattr(review, "findings")
        assert hasattr(review, "confidence")
```

**Why it's bad**: Tests Pydantic model structure, not behavior. Model changes are implementation details.

---

## Prism Patterns

### Testing Async Nodes

```python
import asyncio

class TestReviewNode:
    def test_review_node_returns_verdict(self):
        state = {"files_changed": "x.py", "diff": "+line"}
        mock_verdict = {
            "summary": "OK",
            "critical_findings": [],
            "major_findings": [],
            "minor_findings": [],
            "approved": True,
            "debate_records": [],
        }
        with patch("app.graph.nodes.review_pipeline.get_pipeline") as mock_get:
            mock_pipeline = MagicMock(return_value=mock_verdict)
            mock_get.return_value = mock_pipeline
            result = asyncio.run(run_review_pipeline(state))
            assert result["approved"] is True
```

### Testing Pydantic Models

```python
class TestFinding:
    def test_severity_must_be_valid_literal(self):
        finding = Finding(
            finding="x",
            severity="critical",
            confidence=0.9,
            evidence="code snippet",
            recommendation="fix it",
        )
        assert finding.severity == "critical"

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            Finding(
                finding="x",
                severity="critical",
                confidence=1.5,  # out of range
                evidence="e",
                recommendation="r",
            )
```
