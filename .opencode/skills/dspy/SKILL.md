---
name: dspy
description: DSPy Signatures, Modules, ChainOfThought, and optimizers. Use when user mentions "dspy", "signature", "module", "chain of thought", "optimizer". Triggers on DSPy questions.
---

# DSPy Conventions

## Signatures

```python
import dspy

class ReviewSignature(dspy.Signature):
    """Review code for issues."""
    files_changed: str = dspy.InputField()
    diff: str = dspy.InputField()
    critical_findings: list[str] = dspy.OutputField()
    major_findings: list[str] = dspy.OutputField()
    minor_findings: list[str] = dspy.OutputField()
```

## Modules

```python
class ReviewAgent(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(ReviewSignature)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        return {
            "critical_findings": result.critical_findings,
            "major_findings": result.major_findings,
            "minor_findings": result.minor_findings,
        }
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

- No embedded prompt strings
- Signatures define I/O contracts
- Modules compose signatures
- ChainOfThought adds reasoning
- Optimizers improve prompts from examples

## Checklist

Before writing DSPy code:

```bash
mypy app/
```
