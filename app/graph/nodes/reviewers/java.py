from app.core.models import FileChange, Language
from app.graph.nodes.reviewers.base import BaseReviewer
from app.llm.prompts import JAVA_REVIEWER_PROMPT


class JavaReviewer(BaseReviewer):
    """Java code reviewer using Google Java Style + LLM."""

    @property
    def language(self) -> Language:
        return Language.JAVA

    @property
    def system_prompt(self) -> str:
        return JAVA_REVIEWER_PROMPT

    def _build_user_prompt(self, files: list[FileChange], diff: str) -> str:
        """Build Java-specific user prompt."""
        file_paths = [f.path for f in files]
        return f"Java files changed: {', '.join(file_paths)}\n\nDiff:\n{diff}"
