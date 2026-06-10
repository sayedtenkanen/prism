from abc import ABC, abstractmethod
from typing import Optional

from app.core.models import FileChange, Language, ReviewIssue, ReviewResult
from app.llm.client import LLMClient


class BaseReviewer(ABC):
    """Abstract base class for language-specific reviewers."""

    def __init__(self, llm_client: LLMClient, model: Optional[str] = None):
        self.llm_client = llm_client
        self.model = model

    @property
    @abstractmethod
    def language(self) -> Language:
        """Return the language this reviewer handles."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for the LLM."""
        pass

    @abstractmethod
    def parse_llm_response(self, response: str) -> list[ReviewIssue]:
        """Parse LLM response into structured ReviewIssue objects."""
        pass

    async def review(self, files: list[FileChange], diff: str) -> ReviewResult:
        """Review code changes and return structured feedback."""
        try:
            user_prompt = self._build_user_prompt(files, diff)
            response = await self.llm_client.review(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                model=self.model,
            )
            issues = self.parse_llm_response(response)
            return ReviewResult(
                language=self.language,
                issues=issues,
                summary=response,
                passed=not any(i.severity == "critical" for i in issues),
                tool_output=response,
            )
        except Exception as e:
            return ReviewResult(
                language=self.language,
                issues=[],
                summary=f"Reviewer error: {str(e)}",
                passed=False,
                tool_output=str(e),
            )

    def _build_user_prompt(self, files: list[FileChange], diff: str) -> str:
        """Build the user prompt with file context."""
        file_paths = [f.path for f in files]
        return f"Files changed: {', '.join(file_paths)}\n\nDiff:\n{diff}"
