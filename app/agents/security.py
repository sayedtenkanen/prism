import dspy

from app.agents.base import BaseAgent
from app.agents.signatures import SecurityReview


class SecurityAgent(BaseAgent):
    """Security review agent — checks for OWASP vulnerabilities, injection, auth, secrets, deps."""

    agent_name = "security"

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(SecurityReview)
