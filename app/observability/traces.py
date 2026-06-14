from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SpanKind(str, Enum):
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    CHAIN = "chain"
    RETRIEVAL = "retrieval"


class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    trace_id: str = ""
    parent_span_id: str | None = None
    name: str
    kind: SpanKind = SpanKind.CHAIN
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float = 0.0
    status: str = "ok"
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append(
            {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
        )


class Tracer:
    def __init__(self) -> None:
        self.spans: list[TraceSpan] = []
        self._active: dict[str, TraceSpan] = {}

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.CHAIN,
        parent_span_id: str | None = None,
        trace_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TraceSpan:
        span = TraceSpan(
            name=name,
            kind=kind,
            parent_span_id=parent_span_id,
            trace_id=trace_id or (self.spans[0].trace_id if self.spans else uuid.uuid4().hex),
            attributes=attributes or {},
        )
        self._active[span.span_id] = span
        return span

    def finish_span(self, span_id: str, status: str = "ok") -> TraceSpan | None:
        span = self._active.pop(span_id, None)
        if span:
            span.finish(status)
            self.spans.append(span)
        return span

    def get_trace(self) -> list[TraceSpan]:
        return list(self.spans)

    def get_spans_by_kind(self, kind: SpanKind) -> list[TraceSpan]:
        return [s for s in self.spans if s.kind == kind]

    def get_total_duration_ms(self) -> float:
        if not self.spans:
            return 0.0
        return round(sum(s.duration_ms for s in self.spans), 2)

    def get_trace_summary(self) -> dict[str, Any]:
        by_kind: dict[str, int] = {}
        for span in self.spans:
            by_kind[span.kind.value] = by_kind.get(span.kind.value, 0) + 1

        return {
            "total_spans": len(self.spans),
            "total_duration_ms": self.get_total_duration_ms(),
            "by_kind": by_kind,
            "errors": len([s for s in self.spans if s.status != "ok"]),
        }

    def clear(self) -> None:
        self.spans.clear()
        self._active.clear()
