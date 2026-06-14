from app.eval.metrics import (
    _finding_matches,
    _normalize_finding,
    _severity_matches,
    compute_metrics,
)


class TestComputeMetrics:
    def test_empty_findings(self):
        metrics = compute_metrics([], [])
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1 == 1.0
        assert metrics.accuracy == 1.0
        assert metrics.true_negatives == 1

    def test_perfect_match(self):
        predicted = [{"finding": "SQL injection", "severity": "critical", "file": "app.py", "line": 10}]
        expected = [{"finding": "SQL injection", "severity": "critical", "file": "app.py", "line": 10}]
        metrics = compute_metrics(predicted, expected)
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1 == 1.0
        assert metrics.true_positives == 1

    def test_false_positive(self):
        predicted = [{"finding": "XSS vulnerability", "severity": "high", "file": "app.py"}]
        expected = [{"finding": "SQL injection", "severity": "critical", "file": "app.py"}]
        metrics = compute_metrics(predicted, expected)
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
        assert metrics.false_positives == 1
        assert metrics.false_negatives == 1

    def test_false_negative(self):
        predicted = []
        expected = [{"finding": "SQL injection", "severity": "critical", "file": "app.py"}]
        metrics = compute_metrics(predicted, expected)
        assert metrics.precision == 1.0
        assert metrics.recall == 0.0
        assert metrics.false_negatives == 1

    def test_partial_match(self):
        predicted = [
            {"finding": "SQL injection", "severity": "critical", "file": "app.py"},
            {"finding": "XSS vulnerability", "severity": "high", "file": "web.py"},
        ]
        expected = [{"finding": "SQL injection", "severity": "critical", "file": "app.py"}]
        metrics = compute_metrics(predicted, expected)
        assert metrics.precision == 0.5
        assert metrics.recall == 1.0
        assert metrics.true_positives == 1
        assert metrics.false_positives == 1

    def test_severity_matching(self):
        predicted = [{"finding": "SQL injection", "severity": "critical", "file": "app.py"}]
        expected = [{"finding": "SQL injection", "severity": "high", "file": "app.py"}]
        metrics = compute_metrics(predicted, expected)
        assert metrics.severity_accuracy == 0.0
        assert metrics.true_positives == 1

    def test_file_matching(self):
        predicted = [{"finding": "SQL injection", "severity": "critical", "file": "app.py"}]
        expected = [{"finding": "SQL injection", "severity": "critical", "file": "web.py"}]
        metrics = compute_metrics(predicted, expected)
        assert metrics.file_accuracy == 0.0

    def test_multiple_matches(self):
        predicted = [
            {"finding": "issue1", "severity": "critical", "file": "a.py"},
            {"finding": "issue2", "severity": "high", "file": "b.py"},
            {"finding": "issue3", "severity": "medium", "file": "c.py"},
        ]
        expected = [
            {"finding": "issue1", "severity": "critical", "file": "a.py"},
            {"finding": "issue2", "severity": "high", "file": "b.py"},
        ]
        metrics = compute_metrics(predicted, expected)
        assert metrics.true_positives == 2
        assert metrics.false_positives == 1
        assert metrics.false_negatives == 0

    def test_only_predicted_no_expected(self):
        predicted = [{"finding": "x", "severity": "low", "file": "a.py"}]
        expected = []
        metrics = compute_metrics(predicted, expected)
        assert metrics.precision == 0.0
        assert metrics.recall == 1.0
        assert metrics.false_positives == 1


class TestNormalizeFinding:
    def test_normalizes_keys(self):
        finding = {"finding": "x", "severity": "high", "file": "a.py", "line": 5, "extra": "ignored"}
        result = _normalize_finding(finding)
        assert result == {"finding": "x", "severity": "high", "file": "a.py", "line": 5}


class TestFindingMatches:
    def test_exact_match(self):
        a = {"finding": "x", "file": "a.py", "line": 1}
        b = {"finding": "x", "file": "a.py", "line": 1}
        assert _finding_matches(a, b) is True

    def test_different_finding(self):
        a = {"finding": "x", "file": "a.py", "line": 1}
        b = {"finding": "y", "file": "a.py", "line": 1}
        assert _finding_matches(a, b) is False

    def test_different_file(self):
        a = {"finding": "x", "file": "a.py", "line": 1}
        b = {"finding": "x", "file": "b.py", "line": 1}
        assert _finding_matches(a, b) is False

    def test_different_line(self):
        a = {"finding": "x", "file": "a.py", "line": 1}
        b = {"finding": "x", "file": "a.py", "line": 2}
        assert _finding_matches(a, b) is False

    def test_missing_line(self):
        a = {"finding": "x", "file": "a.py"}
        b = {"finding": "x", "file": "a.py"}
        assert _finding_matches(a, b) is True


class TestSeverityMatches:
    def test_same_severity(self):
        assert _severity_matches({"severity": "critical"}, {"severity": "critical"}) is True

    def test_different_severity(self):
        assert _severity_matches({"severity": "critical"}, {"severity": "high"}) is False
