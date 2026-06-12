from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.scm.github import GitHubClient


class TestGitHubClient:
    def setup_method(self):
        self.client = GitHubClient(token="ghp_test", api_url="https://api.github.com")

    def teardown_method(self):
        pass

    def test_init(self):
        assert self.client.api_url == "https://api.github.com"
        assert "Bearer ghp_test" in self.client.headers["Authorization"]

    def test_init_strips_trailing_slash(self):
        client = GitHubClient(token="ghp_test", api_url="https://api.github.com/")
        assert client.api_url == "https://api.github.com"

    def test_init_strips_multiple_trailing_slashes(self):
        client = GitHubClient(token="ghp_test", api_url="https://api.github.com///")
        assert client.api_url == "https://api.github.com"

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

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
            result = await self.client.get_pr("owner", "repo", 123)
            assert result["number"] == 123
            assert result["title"] == "Test PR"

    @pytest.mark.asyncio
    async def test_get_diff(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "@@ -1,3 +1,4 @@\n+new line\n unchanged\n"
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
            result = await self.client.get_diff("owner", "repo", 123)
            assert "+new line" in result

    @pytest.mark.asyncio
    async def test_get_files_pagination(self):
        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.json.return_value = [{"filename": f"file{i}.py"} for i in range(100)]
        page1_response.raise_for_status = MagicMock()

        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.json.return_value = [{"filename": "file100.py"}]
        page2_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=[page1_response, page2_response])
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
            result = await self.client.get_files("owner", "repo", 123)
            assert len(result) == 101

    @pytest.mark.asyncio
    async def test_get_files_single_page(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"filename": "test.py"}, {"filename": "main.py"}]
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
            result = await self.client.get_files("owner", "repo", 123)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_post_comment(self):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "body": "Review comment"}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
            result = await self.client.post_comment("owner", "repo", 123, "Review comment")
            assert result["body"] == "Review comment"

    @pytest.mark.asyncio
    async def test_get_comments_pagination(self):
        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.json.return_value = [{"id": i, "body": f"Comment {i}"} for i in range(100)]
        page1_response.raise_for_status = MagicMock()

        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.json.return_value = [{"id": 100, "body": "Comment 100"}]
        page2_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=[page1_response, page2_response])
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
            result = await self.client.get_comments("owner", "repo", 123)
            assert len(result) == 101

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

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
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

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False

        with patch.object(self.client, "_get_client", return_value=mock_http_client):
            with pytest.raises(httpx.HTTPStatusError):
                await self.client.get_pr("owner", "repo", 999)

    @pytest.mark.asyncio
    async def test_close(self):
        mock_http_client = AsyncMock()
        mock_http_client.is_closed = False
        mock_http_client.aclose = AsyncMock()
        self.client._client = mock_http_client

        await self.client.close()
        mock_http_client.aclose.assert_called_once()
