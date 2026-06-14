from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class BenchmarkCase(BaseModel):
    case_id: str
    files_changed: str
    diff: str
    expected_findings: list[dict[str, Any]] = Field(default_factory=list)
    expected_severity: Literal["critical", "high", "medium", "low", "info"] | None = None
    language: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkDataset(BaseModel):
    name: str
    version: str = "1.0.0"
    cases: list[BenchmarkCase] = Field(default_factory=list)
    description: str = ""
    source: str = ""

    def filter_by_language(self, language: str) -> BenchmarkDataset:
        filtered = [c for c in self.cases if c.language == language]
        return BenchmarkDataset(
            name=f"{self.name}_{language}",
            version=self.version,
            cases=filtered,
            description=self.description,
            source=self.source,
        )

    def filter_by_tag(self, tag: str) -> BenchmarkDataset:
        filtered = [c for c in self.cases if tag in c.tags]
        return BenchmarkDataset(
            name=f"{self.name}_{tag}",
            version=self.version,
            cases=filtered,
            description=self.description,
            source=self.source,
        )

    def split(self, train_ratio: float = 0.8) -> tuple[BenchmarkDataset, BenchmarkDataset]:
        split_idx = int(len(self.cases) * train_ratio)
        train = BenchmarkDataset(
            name=f"{self.name}_train",
            version=self.version,
            cases=self.cases[:split_idx],
            description=self.description,
            source=self.source,
        )
        test = BenchmarkDataset(
            name=f"{self.name}_test",
            version=self.version,
            cases=self.cases[split_idx:],
            description=self.description,
            source=self.source,
        )
        return train, test


def load_benchmark(path: str | Path) -> BenchmarkDataset:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {path}")

    with open(path) as f:
        data = json.load(f)

    if isinstance(data, list):
        cases = [BenchmarkCase(**item) for item in data]
        return BenchmarkDataset(name=path.stem, cases=cases)

    return BenchmarkDataset(**data)


def save_benchmark(dataset: BenchmarkDataset, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(dataset.model_dump(), f, indent=2)
