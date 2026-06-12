from typing import Any

import httpx

from app.scm.client import SCMClient


class GitHubClient(SCMClient):
    """GitHub REST API v3 client."""

    def __init__(self, token: str, api_url: str = "https://api.github.com"):
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Fetch PR metadata."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def get_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch PR diff."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    async def get_files(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch list of changed files in PR."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json()
            return result

    async def post_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        """Post a comment on the PR."""
        url = f"{self.api_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": body}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def get_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all comments on the PR."""
        url = f"{self.api_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json()
            return result

    async def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = "main") -> str:
        """Fetch file content from repo."""
        url = f"{self.api_url}/repos/{owner}/{repo}/contents/{file_path}"
        params = {"ref": ref}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            import base64

            content: str = data.get("content", "")
            encoding: str = data.get("encoding", "")
            if encoding == "base64":
                decoded: str = base64.b64decode(content).decode("utf-8", errors="replace")
                return decoded
            return content
