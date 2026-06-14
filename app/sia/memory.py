from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    pr_id: str
    repo: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    verdict: str = ""
    summary: str = ""
    languages: list[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryStore:
    def __init__(self, max_entries: int = 1000) -> None:
        self.max_entries = max_entries
        self._entries: list[MemoryEntry] = []
        self._index: dict[str, list[int]] = {}

    def add(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)
        idx = len(self._entries) - 1
        self._index.setdefault(entry.repo, []).append(idx)
        self._index.setdefault(entry.pr_id, []).append(idx)
        if len(self._entries) > self.max_entries:
            self._evict()

    def get(self, entry_id: str) -> MemoryEntry | None:
        for entry in self._entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def get_by_pr(self, pr_id: str) -> list[MemoryEntry]:
        indices = self._index.get(pr_id, [])
        return [self._entries[i] for i in indices if i < len(self._entries)]

    def get_by_repo(self, repo: str, limit: int = 10) -> list[MemoryEntry]:
        indices = self._index.get(repo, [])
        return [self._entries[i] for i in indices[-limit:] if i < len(self._entries)]

    def search_by_language(self, language: str, limit: int = 10) -> list[MemoryEntry]:
        results = [e for e in self._entries if language in e.languages]
        return results[-limit:]

    def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        return list(self._entries[-limit:])

    def count(self) -> int:
        return len(self._entries)

    def delete(self, entry_id: str) -> bool:
        for i, entry in enumerate(self._entries):
            if entry.entry_id == entry_id:
                self._entries.pop(i)
                self._rebuild_index()
                return True
        return False

    def clear(self) -> None:
        self._entries.clear()
        self._index.clear()

    def _evict(self) -> None:
        excess = len(self._entries) - self.max_entries
        if excess > 0:
            self._entries = self._entries[excess:]
            self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._index.clear()
        for i, entry in enumerate(self._entries):
            self._index.setdefault(entry.repo, []).append(i)
            self._index.setdefault(entry.pr_id, []).append(i)

    def get_summary(self) -> dict[str, Any]:
        repos = set()
        languages: dict[str, int] = {}
        for entry in self._entries:
            repos.add(entry.repo)
            for lang in entry.languages:
                languages[lang] = languages.get(lang, 0) + 1
        return {
            "total_entries": len(self._entries),
            "unique_repos": len(repos),
            "languages": languages,
            "max_entries": self.max_entries,
        }
