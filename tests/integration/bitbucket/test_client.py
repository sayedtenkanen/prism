from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.bitbucket.client import BitbucketClient


class TestBitbucketClient:
    def test_init(self):
        client = BitbucketClient(
            base_url="https://bitbucket.example.com",
            token="test-token",
        )
        assert client.base_url == "https://bitbucket.example.com"
        assert client.token == "test-token"
        assert client.headers["Authorization"] == "Bearer test-token"
        assert client.headers["Accept"] == "application/json"

    def test_init_strips_trailing_slash(self):
        client = BitbucketClient(
            base_url="https://bitbucket.example.com/",
            token="test-token",
        )
        assert client.base_url == "https://bitbucket.example.com"

    @pytest.mark.asyncio
    async def test_get_pr(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test PR",
            "author": {"user": {"name": "testuser"}},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.bitbucket.client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)

            client = BitbucketClient(
                base_url="https://bitbucket.example.com",
                token="test-token",
            )
            result = await client.get_pr("TEST", "repo", "123")

            assert result["id"] == 123
            assert result["title"] == "Test PR"

    @pytest.mark.asyncio
    async def test_get_diff(self):
        mock_response = MagicMock()
        mock_response.text = "@@ -1,5 +1,10 @@\n+new line"
        mock_response.raise_for_status = MagicMock()

        with patch("app.bitbucket.client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)

            client = BitbucketClient(
                base_url="https://bitbucket.example.com",
                token="test-token",
            )
            result = await client.get_diff("TEST", "repo", "123")

            assert "@@ -1,5 +1,10 @@" in result

    @pytest.mark.asyncio
    async def test_get_changes(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "values": [
                {"path": {"toString": "src/main.py"}},
                {"path": {"toString": "tests/test_main.py"}},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.bitbucket.client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)

            client = BitbucketClient(
                base_url="https://bitbucket.example.com",
                token="test-token",
            )
            result = await client.get_changes("TEST", "repo", "123")

            assert len(result) == 2
            assert result[0]["path"]["toString"] == "src/main.py"

    @pytest.mark.asyncio
    async def test_post_comment(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 456, "text": "Review posted"}
        mock_response.raise_for_status = MagicMock()

        with patch("app.bitbucket.client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)

            client = BitbucketClient(
                base_url="https://bitbucket.example.com",
                token="test-token",
            )
            result = await client.post_comment("TEST", "repo", "123", "Review summary")

            assert result["id"] == 456

    @pytest.mark.asyncio
    async def test_get_comments(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "values": [
                {"id": 1, "text": "Comment 1"},
                {"id": 2, "text": "Comment 2"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.bitbucket.client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)

            client = BitbucketClient(
                base_url="https://bitbucket.example.com",
                token="test-token",
            )
            result = await client.get_comments("TEST", "repo", "123")

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_file_content(self):
        mock_response = MagicMock()
        mock_response.text = "print('hello')"
        mock_response.raise_for_status = MagicMock()

        with patch("app.bitbucket.client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)

            client = BitbucketClient(
                base_url="https://bitbucket.example.com",
                token="test-token",
            )
            result = await client.get_file_content("TEST", "repo", "src/main.py", "main")

            assert "print('hello')" in result

    @pytest.mark.asyncio
    async def test_get_pr_http_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        with patch("app.bitbucket.client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)

            client = BitbucketClient(
                base_url="https://bitbucket.example.com",
                token="test-token",
            )
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_pr("TEST", "repo", "999")