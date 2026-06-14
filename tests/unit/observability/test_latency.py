import time

from app.observability.latency import LatencyTracker, NodeLatency


class TestNodeLatency:
    def test_creation(self):
        record = NodeLatency(node_name="test-node")
        assert record.node_name == "test-node"
        assert record.start_time > 0
        assert record.end_time is None
        assert record.duration_ms == 0.0
        assert record.status == "ok"

    def test_creation_with_defaults(self):
        record = NodeLatency(node_name="test-node")
        assert record.error is None


class TestLatencyTracker:
    def test_init(self):
        tracker = LatencyTracker()
        assert tracker.records == []
        assert tracker._active == {}

    def test_start(self):
        tracker = LatencyTracker()
        record = tracker.start("fetch_pr")
        assert record.node_name == "fetch_pr"
        assert "fetch_pr" in tracker._active

    def test_finish(self):
        tracker = LatencyTracker()
        tracker.start("fetch_pr")
        time.sleep(0.001)
        result = tracker.finish("fetch_pr")
        assert result is not None
        assert result.duration_ms >= 0.0
        assert "fetch_pr" not in tracker._active
        assert result in tracker.records

    def test_finish_with_error(self):
        tracker = LatencyTracker()
        tracker.start("fetch_pr")
        result = tracker.finish("fetch_pr", status="error", error="timeout")
        assert result is not None
        assert result.status == "error"
        assert result.error == "timeout"

    def test_finish_nonexistent_node(self):
        tracker = LatencyTracker()
        result = tracker.finish("nonexistent")
        assert result is None

    def test_get_latency(self):
        tracker = LatencyTracker()
        tracker.start("fetch_pr")
        time.sleep(0.001)
        tracker.finish("fetch_pr")
        latency = tracker.get_latency("fetch_pr")
        assert latency is not None
        assert latency >= 0.0

    def test_get_latency_no_records(self):
        tracker = LatencyTracker()
        latency = tracker.get_latency("nonexistent")
        assert latency is None

    def test_get_latency_multiple_records(self):
        tracker = LatencyTracker()
        for _ in range(3):
            tracker.start("fetch_pr")
            time.sleep(0.001)
            tracker.finish("fetch_pr")
        latency = tracker.get_latency("fetch_pr")
        assert latency is not None
        assert latency >= 0.0

    def test_get_total_latency(self):
        tracker = LatencyTracker()
        tracker.start("fetch_pr")
        time.sleep(0.001)
        tracker.finish("fetch_pr")
        tracker.start("detect")
        time.sleep(0.001)
        tracker.finish("detect")
        total = tracker.get_total_latency()
        assert total >= 0.0

    def test_get_slowest_nodes(self):
        tracker = LatencyTracker()
        for _ in range(5):
            tracker.start("fast_node")
            tracker.finish("fast_node")
        tracker.start("slow_node")
        time.sleep(0.01)
        tracker.finish("slow_node")
        slowest = tracker.get_slowest_nodes(top_n=1)
        assert len(slowest) == 1
        assert slowest[0]["node_name"] == "slow_node"

    def test_get_slowest_nodes_empty(self):
        tracker = LatencyTracker()
        slowest = tracker.get_slowest_nodes()
        assert slowest == []

    def test_get_slowest_nodes_top_n(self):
        tracker = LatencyTracker()
        for i in range(5):
            tracker.start(f"node_{i}")
            time.sleep(0.001)
            tracker.finish(f"node_{i}")
        slowest = tracker.get_slowest_nodes(top_n=3)
        assert len(slowest) == 3

    def test_get_summary(self):
        tracker = LatencyTracker()
        tracker.start("fetch_pr")
        time.sleep(0.001)
        tracker.finish("fetch_pr")
        summary = tracker.get_summary()
        assert summary["total_latency_ms"] >= 0.0
        assert summary["num_nodes"] == 1
        assert len(summary["slowest_nodes"]) == 1
        assert summary["errors"] == 0

    def test_get_summary_empty(self):
        tracker = LatencyTracker()
        summary = tracker.get_summary()
        assert summary["total_latency_ms"] == 0.0
        assert summary["num_nodes"] == 0

    def test_clear(self):
        tracker = LatencyTracker()
        tracker.start("fetch_pr")
        tracker.finish("fetch_pr")
        tracker.clear()
        assert tracker.records == []
        assert tracker._active == {}
