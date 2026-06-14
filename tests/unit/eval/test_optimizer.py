from unittest.mock import MagicMock, patch

import pytest

from app.eval.benchmark import BenchmarkCase, BenchmarkDataset
from app.eval.optimizer import ReviewOptimizer


class TestReviewOptimizer:
    def test_init(self):
        optimizer = ReviewOptimizer()
        assert optimizer.train_size == 5
        assert optimizer.val_size == 2
        assert "bootstrap_fewshot" in optimizer.optimizers
        assert "labeled_fewshot" in optimizer.optimizers

    def test_custom_init(self):
        optimizer = ReviewOptimizer(train_size=10, val_size=3, max_bootstrapped_demos=8)
        assert optimizer.train_size == 10
        assert optimizer.max_bootstrapped_demos == 8

    def test_prepare_examples(self):
        optimizer = ReviewOptimizer()
        cases = [BenchmarkCase(case_id="1", files_changed="a.py", diff="+x", expected_findings=[{"finding": "y"}])]
        dataset = BenchmarkDataset(name="test", cases=cases)
        examples = optimizer.prepare_examples(dataset)
        assert len(examples) == 1
        assert examples[0].files_changed == "a.py"

    def test_optimize_unknown_optimizer(self):
        optimizer = ReviewOptimizer()
        dataset = BenchmarkDataset(name="test")
        with pytest.raises(ValueError, match="Unknown optimizer"):
            optimizer.optimize(dataset, optimizer_name="nonexistent")

    def test_evaluate_empty_dataset(self):
        optimizer = ReviewOptimizer()
        pipeline = MagicMock()
        dataset = BenchmarkDataset(name="test")
        result = optimizer.evaluate(pipeline, dataset)
        assert result["total_cases"] == 0
        assert result["avg_f1"] == 0.0

    def test_evaluate_with_findings(self):
        optimizer = ReviewOptimizer()
        pipeline = MagicMock(
            return_value={
                "critical_findings": [{"finding": "x", "severity": "critical", "file": "a.py"}],
                "major_findings": [],
                "minor_findings": [],
            }
        )
        cases = [
            BenchmarkCase(
                case_id="1",
                files_changed="a.py",
                diff="+x",
                expected_findings=[{"finding": "x", "severity": "critical", "file": "a.py"}],
            )
        ]
        dataset = BenchmarkDataset(name="test", cases=cases)
        result = optimizer.evaluate(pipeline, dataset)
        assert result["total_cases"] == 1
        assert result["avg_f1"] == 1.0

    def test_evaluate_handles_exception(self):
        optimizer = ReviewOptimizer()
        pipeline = MagicMock(side_effect=Exception("LLM error"))
        cases = [BenchmarkCase(case_id="1", files_changed="a.py", diff="+x")]
        dataset = BenchmarkDataset(name="test", cases=cases)
        result = optimizer.evaluate(pipeline, dataset)
        assert result["total_cases"] == 1
        assert result["avg_f1"] == 0.0

    def test_cross_validate(self):
        optimizer = ReviewOptimizer()
        cases = [BenchmarkCase(case_id=str(i), files_changed="a.py", diff="+x") for i in range(10)]
        dataset = BenchmarkDataset(name="test", cases=cases)

        mock_pipeline = MagicMock(
            return_value={
                "critical_findings": [],
                "major_findings": [],
                "minor_findings": [],
            }
        )

        with patch.object(optimizer, "optimize", return_value=mock_pipeline):
            result = optimizer.cross_validate(dataset, k_folds=2)
            assert result["k_folds"] == 2
            assert len(result["fold_results"]) == 2

    def test_cross_validate_distributes_remainder(self):
        optimizer = ReviewOptimizer()
        cases = [BenchmarkCase(case_id=str(i), files_changed="a.py", diff="+x") for i in range(10)]
        dataset = BenchmarkDataset(name="test", cases=cases)

        mock_pipeline = MagicMock(
            return_value={
                "critical_findings": [],
                "major_findings": [],
                "minor_findings": [],
            }
        )

        with patch.object(optimizer, "optimize", return_value=mock_pipeline):
            result = optimizer.cross_validate(dataset, k_folds=3)
            assert result["k_folds"] == 3
            assert len(result["fold_results"]) == 3
            total_test = sum(len(r["metrics_per_case"]) for r in result["fold_results"])
            assert total_test == 10

    def test_cross_validate_invalid_k_folds_zero(self):
        optimizer = ReviewOptimizer()
        dataset = BenchmarkDataset(name="test", cases=[BenchmarkCase(case_id="1", files_changed="a.py", diff="+x")])
        with pytest.raises(ValueError, match="k_folds must be >= 1"):
            optimizer.cross_validate(dataset, k_folds=0)

    def test_cross_validate_k_folds_exceeds_dataset(self):
        optimizer = ReviewOptimizer()
        dataset = BenchmarkDataset(
            name="test",
            cases=[BenchmarkCase(case_id="1", files_changed="a.py", diff="+x")],
        )
        with pytest.raises(ValueError, match="k_folds .* cannot exceed dataset size"):
            optimizer.cross_validate(dataset, k_folds=5)
