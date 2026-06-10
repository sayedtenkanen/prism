import re
from abc import ABC, abstractmethod
from typing import Optional

from app.core.models import FileChange, Language, ReviewIssue, ReviewResult, ReviewSeverity
from app.llm.client import LLMClient

SEVERITY_MAP: dict[str, ReviewSeverity] = {
    "CRITICAL": ReviewSeverity.CRITICAL,
    "WARNING": ReviewSeverity.WARNING,
    "INFO": ReviewSeverity.INFO,
}

DEFAULT_SEVERITY = ReviewSeverity.INFO


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

    def parse_llm_response(self, response: str) -> list[ReviewIssue]:
        """Parse LLM response into structured ReviewIssue objects.

        Expected format per issue:
            [SEVERITY] path/to/file.py:123 - Message text
            [SEVERITY] path/to/file.py - Message text  (line optional)
        """
        pattern = r"\[(\w+)\]\s*([^:]+):(\d+)?\s*-\s*(.+)"
        matches = re.findall(pattern, response)

        issues: list[ReviewIssue] = []
        for severity_str, file_path, line_str, message in matches:
            severity = self._parse_severity(severity_str)
            line = int(line_str) if line_str else None
            issues.append(
                ReviewIssue(
                    file=file_path.strip(),
                    line=line,
                    severity=severity,
                    message=message.strip(),
                )
            )
        return issues

    def _parse_severity(self, severity_str: str) -> ReviewSeverity:
        """Parse severity string to ReviewSeverity enum."""
        key = severity_str.strip().upper()
        return SEVERITY_MAP.get(key, DEFAULT_SEVERITY)

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
                passed=not any(i.severity == ReviewSeverity.CRITICAL for i in issues),
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
