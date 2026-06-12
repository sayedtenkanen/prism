import json
from typing import Any

import dspy

from app.agents.signatures import SecurityReview


class SecurityAgent(dspy.Module):
    """Security review agent — checks for OWASP vulnerabilities, injection, auth, secrets, deps."""

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(SecurityReview)

    def forward(self, files_changed: str, diff: str) -> dict[str, Any]:
        result = self.review(files_changed=files_changed, diff=diff)
        try:
            findings = json.loads(result.findings)
        except (json.JSONDecodeError, TypeError):
            findings = []
        return {"agent_name": "security", "findings": findings, "reasoning": result.rationale}
