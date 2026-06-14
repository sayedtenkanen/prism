from app.observability.traces import SpanKind, Tracer, TraceSpan


class TestTraceSpan:
    def test_creation(self):
        span = TraceSpan(name="test-span", kind=SpanKind.AGENT)
        assert span.name == "test-span"
        assert span.kind == SpanKind.AGENT
        assert span.span_id
        assert span.status == "ok"
        assert span.duration_ms == 0.0

    def test_finish(self):
        span = TraceSpan(name="test-span")
        span.finish()
        assert span.end_time is not None
        assert span.duration_ms >= 0.0

    def test_finish_with_status(self):
        span = TraceSpan(name="test-span")
        span.finish(status="error")
        assert span.status == "error"

    def test_add_event(self):
        span = TraceSpan(name="test-span")
        span.add_event("llm_call", {"model": "gpt-4o"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "llm_call"

    def test_add_event_no_attributes(self):
        span = TraceSpan(name="test-span")
        span.add_event("start")
        assert span.events[0]["attributes"] == {}


class TestTracer:
    def test_init(self):
        tracer = Tracer()
        assert tracer.spans == []
        assert tracer._active == {}

    def test_start_span(self):
        tracer = Tracer()
        span = tracer.start_span("test-span", kind=SpanKind.AGENT)
        assert span.name == "test-span"
        assert span.span_id in tracer._active

    def test_finish_span(self):
        tracer = Tracer()
        span = tracer.start_span("test-span")
        result = tracer.finish_span(span.span_id)
        assert result is not None
        assert result.duration_ms >= 0.0
        assert span.span_id not in tracer._active
        assert result in tracer.spans

    def test_finish_nonexistent_span(self):
        tracer = Tracer()
        result = tracer.finish_span("nonexistent")
        assert result is None

    def test_get_trace(self):
        tracer = Tracer()
        span1 = tracer.start_span("span1")
        tracer.finish_span(span1.span_id)
        span2 = tracer.start_span("span2")
        tracer.finish_span(span2.span_id)
        trace = tracer.get_trace()
        assert len(trace) == 2

    def test_get_spans_by_kind(self):
        tracer = Tracer()
        agent_span = tracer.start_span("agent", kind=SpanKind.AGENT)
        tracer.finish_span(agent_span.span_id)
        llm_span = tracer.start_span("llm", kind=SpanKind.LLM)
        tracer.finish_span(llm_span.span_id)
        agent_spans = tracer.get_spans_by_kind(SpanKind.AGENT)
        assert len(agent_spans) == 1
        assert agent_spans[0].kind == SpanKind.AGENT

    def test_get_total_duration_ms(self):
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.finish_span(span.span_id)
        total = tracer.get_total_duration_ms()
        assert total >= 0.0

    def test_get_total_duration_ms_no_spans(self):
        tracer = Tracer()
        total = tracer.get_total_duration_ms()
        assert total == 0.0

    def test_get_trace_summary(self):
        tracer = Tracer()
        span = tracer.start_span("test", kind=SpanKind.LLM)
        tracer.finish_span(span.span_id)
        summary = tracer.get_trace_summary()
        assert summary["total_spans"] == 1
        assert summary["total_duration_ms"] >= 0.0
        assert summary["by_kind"]["llm"] == 1
        assert summary["errors"] == 0

    def test_clear(self):
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.finish_span(span.span_id)
        tracer.clear()
        assert tracer.spans == []
        assert tracer._active == {}

    def test_parent_span_id(self):
        tracer = Tracer()
        parent = tracer.start_span("parent")
        child = tracer.start_span("child", parent_span_id=parent.span_id)
        assert child.parent_span_id == parent.span_id
