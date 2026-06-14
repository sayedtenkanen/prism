from __future__ import annotations

from typing import Any

import dspy

from app.agents.modules import FullReviewPipeline
from app.eval.benchmark import BenchmarkDataset
from app.eval.metrics import EvaluationMetrics, compute_metrics


class ReviewOptimizer:
    def __init__(
        self,
        train_size: int = 5,
        val_size: int = 2,
        max_bootstrapped_demos: int = 4,
        max_labeled_demos: int = 16,
    ) -> None:
        self.train_size = train_size
        self.val_size = val_size
        self.max_bootstrapped_demos = max_bootstrapped_demos
        self.max_labeled_demos = max_labeled_demos
        self.optimizers: dict[str, Any] = {
            "bootstrap_fewshot": dspy.BootstrapFewShot(
                metric=self._evaluation_metric,
                max_bootstrapped_demos=self.max_bootstrapped_demos,
                max_labeled_demos=self.max_labeled_demos,
            ),
            "labeled_fewshot": dspy.LabeledFewShot(
                k=self.max_labeled_demos,
            ),
        }

    def _evaluation_metric(
        self,
        example: dspy.Example,
        pred: dict[str, Any],
        trace: Any = None,
    ) -> float:
        expected = example.expected_findings
        predicted = pred.get("critical_findings", []) + pred.get("major_findings", []) + pred.get("minor_findings", [])
        metrics = compute_metrics(predicted, expected)
        return metrics.f1

    def prepare_examples(self, dataset: BenchmarkDataset) -> list[dspy.Example]:
        examples = []
        for case in dataset.cases:
            example = dspy.Example(
                files_changed=case.files_changed,
                diff=case.diff,
                expected_findings=case.expected_findings,
            ).with_inputs("files_changed", "diff")
            examples.append(example)
        return examples

    def optimize(
        self,
        dataset: BenchmarkDataset,
        optimizer_name: str = "bootstrap_fewshot",
    ) -> FullReviewPipeline:
        if optimizer_name not in self.optimizers:
            raise ValueError(f"Unknown optimizer: {optimizer_name}. Available: {list(self.optimizers.keys())}")

        train_dataset, val_dataset = dataset.split(train_ratio=0.8)
        train_examples = self.prepare_examples(train_dataset)
        val_examples = self.prepare_examples(val_dataset)

        optimizer = self.optimizers[optimizer_name]
        pipeline = FullReviewPipeline()

        optimized = optimizer.compile(
            pipeline,
            trainset=train_examples[: self.train_size],
            valset=val_examples[: self.val_size] if val_examples else None,
        )

        return optimized  # type: ignore[no-any-return]

    def evaluate(
        self,
        pipeline: FullReviewPipeline,
        dataset: BenchmarkDataset,
    ) -> dict[str, Any]:
        all_metrics: list[EvaluationMetrics] = []

        for case in dataset.cases:
            try:
                result = pipeline(files_changed=case.files_changed, diff=case.diff)
                critical = result.get("critical_findings", [])
                major = result.get("major_findings", [])
                minor = result.get("minor_findings", [])
                predicted = critical + major + minor
                metrics = compute_metrics(predicted, case.expected_findings)
                all_metrics.append(metrics)
            except Exception:
                all_metrics.append(EvaluationMetrics())

        if not all_metrics:
            return {"avg_precision": 0.0, "avg_recall": 0.0, "avg_f1": 0.0, "total_cases": 0}

        avg_precision = sum(m.precision for m in all_metrics) / len(all_metrics)
        avg_recall = sum(m.recall for m in all_metrics) / len(all_metrics)
        avg_f1 = sum(m.f1 for m in all_metrics) / len(all_metrics)
        avg_accuracy = sum(m.accuracy for m in all_metrics) / len(all_metrics)

        return {
            "avg_precision": round(avg_precision, 4),
            "avg_recall": round(avg_recall, 4),
            "avg_f1": round(avg_f1, 4),
            "avg_accuracy": round(avg_accuracy, 4),
            "total_cases": len(dataset.cases),
            "metrics_per_case": [m.model_dump() for m in all_metrics],
        }

    def cross_validate(
        self,
        dataset: BenchmarkDataset,
        k_folds: int = 5,
        optimizer_name: str = "bootstrap_fewshot",
    ) -> dict[str, Any]:
        if k_folds < 1:
            raise ValueError(f"k_folds must be >= 1, got {k_folds}")
        if k_folds > len(dataset.cases):
            raise ValueError(f"k_folds ({k_folds}) cannot exceed dataset size ({len(dataset.cases)})")

        fold_size = len(dataset.cases) // k_folds
        remainder = len(dataset.cases) % k_folds
        fold_results: list[dict[str, Any]] = []

        offset = 0
        for i in range(k_folds):
            extra = 1 if i < remainder else 0
            test_start = offset
            test_end = offset + fold_size + extra
            test_cases = dataset.cases[test_start:test_end]
            train_cases = dataset.cases[:test_start] + dataset.cases[test_end:]
            offset = test_end

            train_dataset = BenchmarkDataset(
                name=f"{dataset.name}_fold_{i}_train",
                cases=train_cases,
            )
            test_dataset = BenchmarkDataset(
                name=f"{dataset.name}_fold_{i}_test",
                cases=test_cases,
            )

            optimized = self.optimize(train_dataset, optimizer_name=optimizer_name)
            eval_result = self.evaluate(optimized, test_dataset)
            fold_results.append(eval_result)

        avg_f1 = sum(r["avg_f1"] for r in fold_results) / len(fold_results) if fold_results else 0.0

        return {
            "k_folds": k_folds,
            "avg_f1": round(avg_f1, 4),
            "fold_results": fold_results,
        }
