from app.core.models import FileChange, Language
from app.graph.nodes.reviewers.base import BaseReviewer
from app.llm.prompts import ADA_REVIEWER_PROMPT


class AdaReviewer(BaseReviewer):
    """Ada code reviewer using generic Ada conventions + LLM."""

    @property
    def language(self) -> Language:
        return Language.ADA

    @property
    def system_prompt(self) -> str:
        return ADA_REVIEWER_PROMPT

    def _build_user_prompt(self, files: list[FileChange], diff: str) -> str:
        """Build Ada-specific user prompt."""
        file_paths = [f.path for f in files]
        return f"Ada files changed: {', '.join(file_paths)}\n\nDiff:\n{diff}"
