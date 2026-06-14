from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

SeverityLevel = Literal["critical", "high", "medium", "low", "info"]

SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


class EvaluationMetrics(BaseModel):
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    accuracy: float = 0.0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0
    severity_accuracy: float = 0.0
    file_accuracy: float = 0.0


def _normalize_finding(finding: dict[str, Any]) -> dict[str, Any]:
    normalized = {}
    for key in ("finding", "severity", "file", "line"):
        normalized[key] = finding.get(key)
    return normalized


def _finding_matches(predicted: dict[str, Any], expected: dict[str, Any]) -> bool:
    if predicted.get("finding") != expected.get("finding"):
        return False
    if predicted.get("file") != expected.get("file"):
        return False
    if predicted.get("line") != expected.get("line"):
        return False
    return True


def _severity_matches(predicted: dict[str, Any], expected: dict[str, Any]) -> bool:
    return predicted.get("severity") == expected.get("severity")


def compute_metrics(
    predicted_findings: list[dict[str, Any]],
    expected_findings: list[dict[str, Any]],
    severity_weight: float = 0.5,
) -> EvaluationMetrics:
    if not expected_findings and not predicted_findings:
        return EvaluationMetrics(
            precision=1.0,
            recall=1.0,
            f1=1.0,
            accuracy=1.0,
            true_negatives=1,
        )

    if not expected_findings:
        fp = len(predicted_findings)
        return EvaluationMetrics(
            precision=0.0,
            recall=1.0,
            f1=0.0,
            accuracy=0.0,
            false_positives=fp,
        )

    if not predicted_findings:
        fn = len(expected_findings)
        return EvaluationMetrics(
            precision=1.0,
            recall=0.0,
            f1=0.0,
            accuracy=0.0,
            false_negatives=fn,
        )

    tp = 0
    fp = 0
    fn = 0
    severity_correct = 0
    file_correct = 0
    matched_expected: set[int] = set()

    for pred in predicted_findings:
        best_match_idx = -1
        for i, exp in enumerate(expected_findings):
            if i in matched_expected:
                continue
            if _finding_matches(pred, exp):
                best_match_idx = i
                break

        if best_match_idx >= 0:
            tp += 1
            matched_expected.add(best_match_idx)
            if _severity_matches(pred, expected_findings[best_match_idx]):
                severity_correct += 1
            if pred.get("file") == expected_findings[best_match_idx].get("file"):
                file_correct += 1
        else:
            fp += 1

    fn = len(expected_findings) - len(matched_expected)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    total = tp + fp + fn
    accuracy = tp / total if total > 0 else 0.0
    severity_acc = severity_correct / tp if tp > 0 else 0.0
    file_acc = file_correct / tp if tp > 0 else 0.0

    return EvaluationMetrics(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        accuracy=round(accuracy, 4),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        severity_accuracy=round(severity_acc, 4),
        file_accuracy=round(file_acc, 4),
    )
