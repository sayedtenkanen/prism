import dspy

from app.agents.base import BaseAgent
from app.agents.signatures import MaintainabilityReview


class MaintainabilityAgent(BaseAgent):
    """Maintainability review agent — checks for complexity, readability, design smells."""

    agent_name = "maintainability"

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(MaintainabilityReview)
