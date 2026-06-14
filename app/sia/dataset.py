from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.sia.feedback import FeedbackAction, FeedbackCollector
from app.sia.memory import MemoryStore


class DatasetEntry(BaseModel):
    entry_id: str
    files_changed: str
    diff: str
    expected_findings: list[dict[str, Any]] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetBuilder:
    def __init__(
        self,
        memory_store: MemoryStore,
        feedback_collector: FeedbackCollector,
    ) -> None:
        self.memory_store = memory_store
        self.feedback_collector = feedback_collector

    def build_from_memory(
        self,
        repo: str | None = None,
        language: str | None = None,
        min_feedback: int = 1,
    ) -> list[DatasetEntry]:
        if repo:
            entries = self.memory_store.get_by_repo(repo, limit=1000)
        elif language:
            entries = self.memory_store.search_by_language(language, limit=1000)
        else:
            entries = self.memory_store.get_recent(limit=1000)

        dataset: list[DatasetEntry] = []
        for entry in entries:
            feedback_items = []
            for finding in entry.findings:
                finding_id = finding.get("finding_id", finding.get("finding", ""))
                fb = self.feedback_collector.get_for_finding(finding_id)
                if len(fb) >= min_feedback:
                    feedback_items.append((finding, fb))

            if not feedback_items:
                continue

            expected = []
            for finding, fb_list in feedback_items:
                accepted = any(f.action == FeedbackAction.ACCEPT for f in fb_list)
                if accepted:
                    expected.append(finding)

            dataset.append(
                DatasetEntry(
                    entry_id=entry.entry_id,
                    files_changed=entry.metadata.get("files_changed", ""),
                    diff=entry.metadata.get("diff", ""),
                    expected_findings=expected,
                    languages=entry.languages,
                    metadata={"pr_id": entry.pr_id, "repo": entry.repo},
                )
            )

        return dataset

    def build_from_findings(
        self,
        pr_id: str,
        repo: str,
        files_changed: str,
        diff: str,
        findings: list[dict[str, Any]],
        accepted_indices: list[int],
    ) -> DatasetEntry:
        expected = [findings[i] for i in accepted_indices if i < len(findings)]
        return DatasetEntry(
            entry_id=pr_id,
            files_changed=files_changed,
            diff=diff,
            expected_findings=expected,
            metadata={"pr_id": pr_id, "repo": repo},
        )

    def export_json(self, dataset: list[DatasetEntry], path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump([entry.model_dump() for entry in dataset], f, indent=2)

    def import_json(self, path: str | Path) -> list[DatasetEntry]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")
        with open(path) as f:
            data = json.load(f)
        return [DatasetEntry(**item) for item in data]

    def filter_entries(
        self,
        dataset: list[DatasetEntry],
        min_findings: int = 1,
        languages: list[str] | None = None,
    ) -> list[DatasetEntry]:
        result = dataset
        if languages:
            result = [e for e in result if any(lang in e.languages for lang in languages)]
        if min_findings > 0:
            result = [e for e in result if len(e.expected_findings) >= min_findings]
        return result

    def get_statistics(self, dataset: list[DatasetEntry]) -> dict[str, Any]:
        if not dataset:
            return {"total_entries": 0, "total_findings": 0, "languages": {}}

        total_findings = sum(len(e.expected_findings) for e in dataset)
        languages: dict[str, int] = {}
        for entry in dataset:
            for lang in entry.languages:
                languages[lang] = languages.get(lang, 0) + 1

        return {
            "total_entries": len(dataset),
            "total_findings": total_findings,
            "avg_findings_per_entry": round(total_findings / len(dataset), 2),
            "languages": languages,
        }
