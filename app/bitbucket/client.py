from typing import Any, Dict, List, Optional

import httpx


class BitbucketClient:
    """Bitbucket Server REST API client."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    async def get_pr(self, project_key: str, repo_slug: str, pr_id: str) -> Dict[str, Any]:
        """Fetch PR metadata."""
        url = f"{self.base_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_diff(self, project_key: str, repo_slug: str, pr_id: str) -> str:
        """Fetch PR diff."""
        url = f"{self.base_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/diff"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text

    async def get_changes(self, project_key: str, repo_slug: str, pr_id: str) -> List[Dict[str, Any]]:
        """Fetch list of changed files in PR."""
        url = f"{self.base_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/changes"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("values", [])

    async def post_comment(self, project_key: str, repo_slug: str, pr_id: str, text: str) -> Dict[str, Any]:
        """Post a comment on the PR."""
        url = f"{self.base_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        payload = {"text": text}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_comments(self, project_key: str, repo_slug: str, pr_id: str) -> List[Dict[str, Any]]:
        """Fetch all comments on the PR."""
        url = f"{self.base_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("values", [])

    async def get_file_content(
        self, project_key: str, repo_slug: str, file_path: str, ref: str = "main"
    ) -> str:
        """Fetch file content from repo."""
        url = f"{self.base_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/raw/{file_path}"
        params = {"at": ref}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.text