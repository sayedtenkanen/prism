from abc import ABC, abstractmethod
from typing import Any


class RAGStore(ABC):
    """Abstract interface for RAG vector storage."""

    @abstractmethod
    async def add(self, document_id: str, text: str, metadata: dict[str, Any]) -> None:
        """Store a document with its embedding."""
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search for similar documents."""
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> None:
        """Delete a document by ID."""
        pass

    @abstractmethod
    async def get(self, document_id: str) -> dict[str, Any] | None:
        """Retrieve a document by ID."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Return the number of stored documents."""
        pass
