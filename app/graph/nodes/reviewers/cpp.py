from app.core.models import FileChange, Language
from app.graph.nodes.reviewers.base import BaseReviewer
from app.llm.prompts import CPP_REVIEWER_PROMPT


class CppReviewer(BaseReviewer):
    """C++ code reviewer using Google C++ Style + LLM."""

    @property
    def language(self) -> Language:
        return Language.CPP

    @property
    def system_prompt(self) -> str:
        return CPP_REVIEWER_PROMPT

    def _build_user_prompt(self, files: list[FileChange], diff: str) -> str:
        """Build C++-specific user prompt."""
        file_paths = [f.path for f in files]
        return f"C++ files changed: {', '.join(file_paths)}\n\nDiff:\n{diff}"
