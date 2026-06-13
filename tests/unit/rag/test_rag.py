from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.pgvector import PGVectorStore
from app.rag.retriever import Retriever
from app.rag.store import RAGStore


class TestRAGStore:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            RAGStore()


class TestPGVectorStore:
    def test_init(self):
        store = PGVectorStore(api_url="http://localhost:8000", api_key="key", collection="test")
        assert store.api_url == "http://localhost:8000"
        assert store.api_key == "key"
        assert store.collection == "test"

    def test_init_defaults(self):
        store = PGVectorStore(api_url="http://localhost:8000/")
        assert store.api_url == "http://localhost:8000"
        assert store.collection == "prism_reviews"

    @pytest.mark.asyncio
    async def test_add(self):
        store = PGVectorStore(api_url="http://localhost:8000")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        with patch.object(store, "_get_client", return_value=mock_client):
            await store.add("doc1", "test text", {"file_path": "test.py"})
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_search(self):
        store = PGVectorStore(api_url="http://localhost:8000")
        mock_response = MagicMock()
        mock_response.json.return_value = [{"text": "found", "score": 0.9}]
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        with patch.object(store, "_get_client", return_value=mock_client):
            results = await store.search("query", top_k=3)
            assert len(results) == 1
            assert results[0]["text"] == "found"

    @pytest.mark.asyncio
    async def test_delete(self):
        store = PGVectorStore(api_url="http://localhost:8000")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        with patch.object(store, "_get_client", return_value=mock_client):
            await store.delete("doc1")
            mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_found(self):
        store = PGVectorStore(api_url="http://localhost:8000")
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "doc1", "text": "content"}
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        with patch.object(store, "_get_client", return_value=mock_client):
            result = await store.get("doc1")
            assert result is not None
            assert result["id"] == "doc1"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        store = PGVectorStore(api_url="http://localhost:8000")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        with patch.object(store, "_get_client", return_value=mock_client):
            result = await store.get("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_count(self):
        store = PGVectorStore(api_url="http://localhost:8000")
        mock_response = MagicMock()
        mock_response.json.return_value = {"count": 42}
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        with patch.object(store, "_get_client", return_value=mock_client):
            count = await store.count()
            assert count == 42

    @pytest.mark.asyncio
    async def test_close(self):
        store = PGVectorStore(api_url="http://localhost:8000")
        mock_client = AsyncMock()
        mock_client.is_closed = False
        store._client = mock_client
        await store.close()
        mock_client.aclose.assert_called_once()


class TestRetriever:
    @pytest.mark.asyncio
    async def test_get_review_context_empty(self):
        store = AsyncMock(spec=RAGStore)
        store.search = AsyncMock(return_value=[])
        retriever = Retriever(store)

        context = await retriever.get_review_context("file.py", "+line")
        assert context == ""

    @pytest.mark.asyncio
    async def test_get_review_context_with_results(self):
        store = AsyncMock(spec=RAGStore)
        store.search = AsyncMock(
            return_value=[
                {"text": "previous finding", "metadata": {"file_path": "app/main.py"}},
                {"text": "another finding", "metadata": {"file_path": "app/utils.py"}},
            ]
        )
        retriever = Retriever(store)

        context = await retriever.get_review_context("file.py", "+line")
        assert "app/main.py" in context
        assert "previous finding" in context
        assert "app/utils.py" in context

    @pytest.mark.asyncio
    async def test_get_similar_findings(self):
        store = AsyncMock(spec=RAGStore)
        store.search = AsyncMock(
            return_value=[
                {"text": "similar", "metadata": {"severity": "high"}, "score": 0.85},
            ]
        )
        retriever = Retriever(store)

        findings = await retriever.get_similar_findings("security issue")
        assert len(findings) == 1
        assert findings[0]["text"] == "similar"
        assert findings[0]["score"] == 0.85
