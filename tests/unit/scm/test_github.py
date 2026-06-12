from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.scm.github import GitHubClient


class TestGitHubClient:
    def setup_method(self):
        self.client = GitHubClient(token="ghp_test", api_url="https://api.github.com")

    def test_init(self):
        assert self.client.api_url == "https://api.github.com"
        assert "Bearer ghp_test" in self.client.headers["Authorization"]

    @pytest.mark.asyncio
    async def test_get_pr(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "number": 123,
            "title": "Test PR",
            "user": {"login": "testuser"},
            "state": "open",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await self.client.get_pr("owner", "repo", 123)
            assert result["number"] == 123
            assert result["title"] == "Test PR"

    @pytest.mark.asyncio
    async def test_get_diff(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "@@ -1,3 +1,4 @@\n+new line\n unchanged\n"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await self.client.get_diff("owner", "repo", 123)
            assert "+new line" in result

    @pytest.mark.asyncio
    async def test_get_files(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"filename": "test.py", "status": "modified", "additions": 5, "deletions": 2},
            {"filename": "new.py", "status": "added", "additions": 10, "deletions": 0},
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await self.client.get_files("owner", "repo", 123)
            assert len(result) == 2
            assert result[0]["filename"] == "test.py"

    @pytest.mark.asyncio
    async def test_post_comment(self):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "body": "Review comment"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await self.client.post_comment("owner", "repo", 123, "Review comment")
            assert result["body"] == "Review comment"

    @pytest.mark.asyncio
    async def test_get_comments(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "body": "Comment 1"},
            {"id": 2, "body": "Comment 2"},
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await self.client.get_comments("owner", "repo", 123)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_file_content(self):
        import base64

        content = base64.b64encode(b"print('hello')").decode()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": content,
            "encoding": "base64",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await self.client.get_file_content("owner", "repo", "test.py")
            assert result == "print('hello')"

    @pytest.mark.asyncio
    async def test_get_pr_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await self.client.get_pr("owner", "repo", 999)
