import dspy

from app.agents.base import BaseAgent
from app.agents.signatures import ArchitectureReview


class ArchitectureAgent(BaseAgent):
    """Architecture review agent — checks for layer violations, coupling, domain consistency."""

    agent_name = "architecture"

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(ArchitectureReview)
