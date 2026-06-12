import base64
from typing import Any

import httpx

from app.scm.client import SCMClient


class GitHubClient(SCMClient):
    """GitHub REST API v3 client with pagination support."""

    def __init__(self, token: str, api_url: str = "https://api.github.com"):
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient()
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def _get_paginated(self, url: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch all pages from a paginated GitHub API endpoint."""
        all_results: list[dict[str, Any]] = []
        client = await self._get_client()
        page = 1
        while True:
            page_params = {"page": page, "per_page": 100, **(params or {})}
            response = await client.get(url, headers=self.headers, params=page_params)
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            all_results.extend(data)
            if len(data) < 100:
                break
            page += 1
        return all_results

    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Fetch PR metadata."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        client = await self._get_client()
        response = await client.get(url, headers=self.headers)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def get_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch PR diff."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        client = await self._get_client()
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    async def get_files(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all changed files in PR (handles pagination)."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        return await self._get_paginated(url)

    async def post_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        """Post a comment on the PR."""
        url = f"{self.api_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": body}
        client = await self._get_client()
        response = await client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def get_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Fetch all comments on the PR (handles pagination)."""
        url = f"{self.api_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        return await self._get_paginated(url)

    async def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = "main") -> str:
        """Fetch file content from repo."""
        url = f"{self.api_url}/repos/{owner}/{repo}/contents/{file_path}"
        params = {"ref": ref}
        client = await self._get_client()
        response = await client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        content: str = data.get("content", "")
        encoding: str = data.get("encoding", "")
        if encoding == "base64":
            decoded: str = base64.b64decode(content).decode("utf-8", errors="replace")
            return decoded
        return content
