import dspy

from app.agents.base import BaseAgent
from app.agents.signatures import TestingReview


class TestingAgent(BaseAgent):
    """Testing review agent — checks for coverage gaps, weak assertions, regression risks."""

    agent_name = "testing"

    def __init__(self) -> None:
        super().__init__()
        self.review = dspy.ChainOfThought(TestingReview)
