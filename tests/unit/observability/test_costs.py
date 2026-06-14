from app.observability.costs import MODEL_COSTS_PER_1K_TOKENS, CostTracker, TokenCost


class TestTokenCost:
    def test_creation(self):
        cost = TokenCost(model="gpt-4o", input_tokens=100, output_tokens=50, total_cost=0.5)
        assert cost.model == "gpt-4o"
        assert cost.input_tokens == 100
        assert cost.output_tokens == 50
        assert cost.total_cost == 0.5
        assert cost.timestamp > 0


class TestCostTracker:
    def test_init(self):
        tracker = CostTracker()
        assert tracker.budget_limit is None
        assert tracker.records == []
        assert tracker._total_cost == 0.0

    def test_init_with_budget(self):
        tracker = CostTracker(budget_limit=10.0)
        assert tracker.budget_limit == 10.0

    def test_record_usage(self):
        tracker = CostTracker()
        record = tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=500)
        assert record.model == "gpt-4o"
        assert record.input_tokens == 1000
        assert record.output_tokens == 500
        assert record.total_cost > 0
        assert len(tracker.records) == 1

    def test_record_usage_calculation(self):
        tracker = CostTracker()
        costs = MODEL_COSTS_PER_1K_TOKENS["gpt-4o"]
        record = tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=1000)
        expected = costs["input"] + costs["output"]
        assert abs(record.total_cost - expected) < 0.0001

    def test_get_total_cost(self):
        tracker = CostTracker()
        tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=500)
        tracker.record_usage("gpt-4o-mini", input_tokens=1000, output_tokens=500)
        total = tracker.get_total_cost()
        assert total > 0

    def test_get_cost_by_model(self):
        tracker = CostTracker()
        tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=500)
        tracker.record_usage("gpt-4o", input_tokens=500, output_tokens=250)
        tracker.record_usage("gpt-4o-mini", input_tokens=1000, output_tokens=500)
        by_model = tracker.get_cost_by_model()
        assert "gpt-4o" in by_model
        assert "gpt-4o-mini" in by_model
        assert by_model["gpt-4o"] > by_model["gpt-4o-mini"]

    def test_get_total_tokens(self):
        tracker = CostTracker()
        tracker.record_usage("gpt-4o", input_tokens=100, output_tokens=50)
        tracker.record_usage("gpt-4o-mini", input_tokens=200, output_tokens=100)
        tokens = tracker.get_total_tokens()
        assert tokens["input"] == 300
        assert tokens["output"] == 150
        assert tokens["total"] == 450

    def test_is_over_budget(self):
        tracker = CostTracker(budget_limit=0.001)
        tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=1000)
        assert tracker.is_over_budget() is True

    def test_is_under_budget(self):
        tracker = CostTracker(budget_limit=100.0)
        tracker.record_usage("gpt-4o", input_tokens=100, output_tokens=50)
        assert tracker.is_over_budget() is False

    def test_is_over_budget_no_limit(self):
        tracker = CostTracker()
        tracker.record_usage("gpt-4o", input_tokens=100000, output_tokens=100000)
        assert tracker.is_over_budget() is False

    def test_get_remaining_budget(self):
        tracker = CostTracker(budget_limit=10.0)
        tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=500)
        remaining = tracker.get_remaining_budget()
        assert remaining is not None
        assert remaining < 10.0

    def test_get_remaining_budget_no_limit(self):
        tracker = CostTracker()
        assert tracker.get_remaining_budget() is None

    def test_get_summary(self):
        tracker = CostTracker(budget_limit=10.0)
        tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=500)
        summary = tracker.get_summary()
        assert summary["total_cost"] > 0
        assert summary["num_requests"] == 1
        assert summary["budget_limit"] == 10.0
        assert summary["over_budget"] is False
        assert "total_tokens" in summary
        assert "cost_by_model" in summary

    def test_clear(self):
        tracker = CostTracker()
        tracker.record_usage("gpt-4o", input_tokens=1000, output_tokens=500)
        tracker.clear()
        assert tracker.records == []
        assert tracker._total_cost == 0.0
