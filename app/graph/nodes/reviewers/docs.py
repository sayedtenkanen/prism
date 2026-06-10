from app.core.models import FileChange, Language
from app.graph.nodes.reviewers.base import BaseReviewer
from app.llm.prompts import DOCS_REVIEWER_PROMPT


class DocsReviewer(BaseReviewer):
    """Documentation reviewer for Markdown files."""

    @property
    def language(self) -> Language:
        return Language.MARKDOWN

    @property
    def system_prompt(self) -> str:
        return DOCS_REVIEWER_PROMPT

    def _build_user_prompt(self, files: list[FileChange], diff: str) -> str:
        """Build documentation-specific user prompt."""
        file_paths = [f.path for f in files]
        return f"Documentation files changed: {', '.join(file_paths)}\n\nDiff:\n{diff}"
