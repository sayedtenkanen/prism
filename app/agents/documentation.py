import dspy

from app.agents.base import BaseAgent
from app.agents.signatures import DocumentationReview


class DocumentationAgent(BaseAgent):
    """Documentation review agent — checks for missing docs, API gaps, changelog requirements."""

    agent_name = "documentation"

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(DocumentationReview)
