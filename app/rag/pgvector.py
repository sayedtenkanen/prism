from typing import Any

import httpx

from app.rag.store import RAGStore


class PGVectorStore(RAGStore):
    """PGVector-backed RAG store via HTTP API."""

    def __init__(self, api_url: str, api_key: str = "", collection: str = "prism_reviews") -> None:
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.collection = collection
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0),
        )

    async def close(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()

    async def add(self, document_id: str, text: str, metadata: dict[str, Any]) -> None:
        payload = {"id": document_id, "text": text, "metadata": metadata, "collection": self.collection}
        response = await self._client.post(f"{self.api_url}/documents", json=payload)
        response.raise_for_status()

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        payload = {"query": query, "top_k": top_k, "collection": self.collection}
        response = await self._client.post(f"{self.api_url}/search", json=payload)
        response.raise_for_status()
        results: list[dict[str, Any]] = response.json()
        return results

    async def delete(self, document_id: str) -> None:
        response = await self._client.delete(
            f"{self.api_url}/documents/{document_id}",
            params={"collection": self.collection},
        )
        response.raise_for_status()

    async def get(self, document_id: str) -> dict[str, Any] | None:
        response = await self._client.get(
            f"{self.api_url}/documents/{document_id}",
            params={"collection": self.collection},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def count(self) -> int:
        response = await self._client.get(f"{self.api_url}/count", params={"collection": self.collection})
        response.raise_for_status()
        result: dict[str, int] = response.json()
        return result.get("count", 0)
