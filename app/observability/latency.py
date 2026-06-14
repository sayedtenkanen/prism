from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field


class NodeLatency(BaseModel):
    node_name: str
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float = 0.0
    status: str = "ok"
    error: str | None = None


class LatencyTracker:
    def __init__(self) -> None:
        self.records: list[NodeLatency] = []
        self._active: dict[str, NodeLatency] = {}

    def start(self, node_name: str) -> NodeLatency:
        if node_name in self._active:
            raise ValueError(f"Node '{node_name}' is already active; finish it before starting again")
        record = NodeLatency(node_name=node_name)
        self._active[node_name] = record
        return record

    def finish(self, node_name: str, status: str = "ok", error: str | None = None) -> NodeLatency | None:
        record = self._active.pop(node_name, None)
        if record:
            record.end_time = time.time()
            record.duration_ms = round((record.end_time - record.start_time) * 1000, 2)
            record.status = status
            record.error = error
            self.records.append(record)
        return record

    def get_latency(self, node_name: str) -> float | None:
        node_records = [r for r in self.records if r.node_name == node_name]
        if not node_records:
            return None
        return round(sum(r.duration_ms for r in node_records) / len(node_records), 2)

    def get_total_latency(self) -> float:
        return round(sum(r.duration_ms for r in self.records), 2)

    def get_slowest_nodes(self, top_n: int = 5) -> list[dict[str, Any]]:
        node_totals: dict[str, float] = {}
        node_counts: dict[str, int] = {}
        for r in self.records:
            node_totals[r.node_name] = node_totals.get(r.node_name, 0.0) + r.duration_ms
            node_counts[r.node_name] = node_counts.get(r.node_name, 0) + 1

        result: list[dict[str, Any]] = []
        for name, total in node_totals.items():
            result.append(
                {
                    "node_name": name,
                    "total_ms": round(total, 2),
                    "avg_ms": round(total / node_counts[name], 2),
                    "count": node_counts[name],
                }
            )
        result.sort(key=lambda x: x["total_ms"], reverse=True)
        return result[:top_n]

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_latency_ms": self.get_total_latency(),
            "num_nodes": len(self.records),
            "slowest_nodes": self.get_slowest_nodes(),
            "errors": len([r for r in self.records if r.status != "ok"]),
        }

    def clear(self) -> None:
        self.records.clear()
        self._active.clear()
