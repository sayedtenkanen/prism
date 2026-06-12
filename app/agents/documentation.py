import json
from typing import Any

import dspy

from app.agents.signatures import DocumentationReview


class DocumentationAgent(dspy.Module):
    """Documentation review agent — checks for missing docs, API gaps, changelog requirements."""

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(DocumentationReview)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        try:
            findings = json.loads(result.findings)
        except (json.JSONDecodeError, TypeError):
            findings = []
        return {"agent_name": "documentation", "findings": findings, "reasoning": result.rationale}
