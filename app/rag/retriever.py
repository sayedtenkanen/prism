from typing import Any

from app.rag.store import RAGStore

DEFAULT_DIFF_LIMIT = 1000


class Retriever:
    """Retrieves relevant context from RAG store for code review."""

    def __init__(self, store: RAGStore, diff_limit: int = DEFAULT_DIFF_LIMIT) -> None:
        self.store = store
        self.diff_limit = diff_limit

    async def get_review_context(self, files_changed: str, diff: str) -> str:
        query = f"code review for:\n{files_changed}\n{diff[: self.diff_limit]}"
        results = await self.store.search(query, top_k=5)
        if not results:
            return ""
        contexts = []
        for r in results:
            text = r.get("text", "")
            metadata = r.get("metadata", {})
            file_path = metadata.get("file_path", "unknown")
            contexts.append(f"--- {file_path} ---\n{text}")
        return "\n\n".join(contexts)

    async def get_similar_findings(self, finding: str) -> list[dict[str, Any]]:
        results = await self.store.search(finding, top_k=3)
        return [
            {"text": r.get("text", ""), "metadata": r.get("metadata", {}), "score": r.get("score", 0.0)}
            for r in results
        ]
