from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.llm.client import LLMClient


class TestLLMClient:
    def test_init_defaults(self):
        with patch("app.llm.client.ChatOpenAI") as mock_openai:
            mock_openai.return_value = MagicMock()
            client = LLMClient(api_key="test-key")
            assert client.provider == "openai"
            assert client.model == "gpt-4o"
            assert client.temperature == 0.3

    def test_init_custom(self):
        with patch("app.llm.client.ChatOpenAI") as mock_openai:
            mock_openai.return_value = MagicMock()
            client = LLMClient(
                provider="ollama",
                model="llama3",
                api_key="test-key",
                temperature=0.5,
            )
            assert client.provider == "ollama"
            assert client.model == "llama3"
            assert client.temperature == 0.5

    @pytest.mark.asyncio
    async def test_ainvoke(self):
        with patch("app.llm.client.ChatOpenAI") as mock_openai:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Test response"
            mock_llm.ainvoke.return_value = mock_response
            mock_openai.return_value = mock_llm

            client = LLMClient(api_key="test-key")
            result = await client.ainvoke([{"role": "user", "content": "Hello"}])

            assert result == "Test response"
            mock_llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_review(self):
        with patch("app.llm.client.ChatOpenAI") as mock_openai:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Review result"
            mock_llm.ainvoke.return_value = mock_response
            mock_openai.return_value = mock_llm

            client = LLMClient(api_key="test-key")
            result = await client.review(
                system_prompt="You are a reviewer",
                user_prompt="Review this code",
            )

            assert result == "Review result"

    @pytest.mark.asyncio
    async def test_review_with_custom_model(self):
        with patch("app.llm.client.ChatOpenAI") as mock_openai:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Custom model result"
            mock_llm.ainvoke.return_value = mock_response
            mock_openai.return_value = mock_llm

            client = LLMClient(api_key="test-key")
            result = await client.review(
                system_prompt="You are a reviewer",
                user_prompt="Review this code",
                model="gpt-3.5-turbo",
            )

            assert result == "Custom model result"
