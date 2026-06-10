from app.core.models import FileChange, Language
from app.graph.nodes.reviewers.base import BaseReviewer
from app.llm.prompts import PYTHON_REVIEWER_PROMPT


class PythonReviewer(BaseReviewer):
    """Python code reviewer using ruff/mypy + LLM."""

    @property
    def language(self) -> Language:
        return Language.PYTHON

    @property
    def system_prompt(self) -> str:
        return PYTHON_REVIEWER_PROMPT

    def _build_user_prompt(self, files: list[FileChange], diff: str) -> str:
        """Build Python-specific user prompt."""
        file_paths = [f.path for f in files]
        return f"Python files changed: {', '.join(file_paths)}\n\nDiff:\n{diff}"
