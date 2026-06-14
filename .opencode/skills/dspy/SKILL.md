---
name: dspy
description: DSPy Signatures, Modules, ChainOfThought, and optimizers. Use when user mentions "dspy", "signature", "module", "chain of thought", "optimizer". Triggers on DSPy questions.
---

# DSPy Conventions

## Signatures

```python
import dspy

class SecurityReview(dspy.Signature):
    """Review code for security vulnerabilities following OWASP guidelines.

    Check for: injection risks, authentication/authorization flaws,
    secrets detection, dependency vulnerabilities, XSS, CSRF,
    SQL injection, path traversal, and insecure configurations.
    """

    files_changed: str = dspy.InputField(desc="List of changed files with their paths and languages")
    diff: str = dspy.InputField(desc="The unified diff of changes")
    findings: str = dspy.OutputField(
        desc="JSON array of findings, each with: finding, severity (critical/high/medium/low/info), "
        "confidence (0.0-1.0), evidence, recommendation, file, line, cwe_id, owasp_category"
    )


class JudgeAggregation(dspy.Signature):
    """Aggregate and deduplicate review findings from multiple agents into a single coherent verdict."""

    all_findings: str = dspy.InputField(
        desc="JSON object with agent_name keys, each containing a JSON array of findings"
    )
    summary: str = dspy.OutputField(desc="Executive summary of the review")
    critical_findings: str = dspy.OutputField(desc="JSON array of critical severity findings")
    major_findings: str = dspy.OutputField(desc="JSON array of high/major severity findings")
    minor_findings: str = dspy.OutputField(desc="JSON array of medium/low/info severity findings")
    approved: bool = dspy.OutputField(desc="Whether the PR is approved (true) or needs changes (false)")
```

## Modules

```python
class SecurityReviewer(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(SecurityReview)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        return parse_findings(result.findings, "security")
```

## Optimizers

```python
# BootstrapFewShot
optimizer = dspy.BootstrapFewShot(
    metric=evaluation_metric,
    max_bootstrapped_demos=4,
    max_labeled_demos=16,
)
optimized = optimizer.compile(pipeline, trainset=train_examples)

# LabeledFewShot
optimizer = dspy.LabeledFewShot(k=16)
```

## Key Patterns

- No embedded prompt strings — Signatures define I/O contracts
- Docstrings contain review context and check lists
- Modules compose signatures with `dspy.ChainOfThought`
- Agents inherit `BaseAgent` and implement `_build_review_signature`
- `parse_findings` helper parses JSON output into structured findings
- Optimizers improve prompts from examples
- InputField `desc` parameter provides field descriptions

## Checklist

Before writing DSPy code:

```bash
ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```
