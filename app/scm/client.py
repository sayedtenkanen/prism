from abc import ABC, abstractmethod
from typing import Any


class SCMClient(ABC):
    """Abstract Source Code Management client protocol."""

    @abstractmethod
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Fetch PR metadata."""
        pass

    @abstractmethod
    async def get_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch PR diff as unified diff string."""
        pass

    @abstractmethod
    async def get_files(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch list of changed files in PR."""
        pass

    @abstractmethod
    async def post_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        """Post a comment on the PR."""
        pass

    @abstractmethod
    async def get_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all comments on the PR."""
        pass

    @abstractmethod
    async def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = "main") -> str:
        """Fetch file content from repo."""
        pass
