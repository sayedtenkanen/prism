import re

from app.core.models import FileChange, Language, ReviewIssue, ReviewSeverity
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

    def parse_llm_response(self, response: str) -> list[ReviewIssue]:
        """Parse LLM response into ReviewIssue objects."""
        issues = []
        pattern = r"\[(\w+)\]\s*([^:]+):(\d+)?\s*-\s*(.+)"
        matches = re.findall(pattern, response)

        for match in matches:
            severity_str, file_path, line_str, message = match
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
        severity_map = {
            "CRITICAL": ReviewSeverity.CRITICAL,
            "WARNING": ReviewSeverity.WARNING,
            "INFO": ReviewSeverity.INFO,
        }
        return severity_map.get(severity_str.upper(), ReviewSeverity.INFO)

    def _build_user_prompt(self, files: list[FileChange], diff: str) -> str:
        """Build Java-specific user prompt."""
        file_paths = [f.path for f in files]
        return f"Java files changed: {', '.join(file_paths)}\n\nDiff:\n{diff}"
