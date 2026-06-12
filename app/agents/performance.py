import dspy

from app.agents.base import BaseAgent
from app.agents.signatures import PerformanceReview


class PerformanceAgent(BaseAgent):
    """Performance review agent — checks for N+1, loops, memory, network, DB issues."""

    agent_name = "performance"

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(PerformanceReview)
