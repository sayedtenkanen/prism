import pytest
from app.core.models import (
    ComparisonResult,
    FileChange,
    FileChangeType,
    Language,
    NodeHealth,
    PRMetadata,
    ReviewIssue,
    ReviewQuality,
    ReviewResult,
    ReviewSeverity,
    TestResult,
    Verdict,
)


class TestLanguage:
    def test_language_values(self):
        assert Language.JAVA == "java"
        assert Language.PYTHON == "python"
        assert Language.CPP == "cpp"
        assert Language.ADA == "ada"
        assert Language.MARKDOWN == "markdown"
        assert Language.UNKNOWN == "unknown"

    def test_language_from_string(self):
        assert Language("java") == Language.JAVA
        assert Language("python") == Language.PYTHON


class TestFileChangeType:
    def test_file_change_type_values(self):
        assert FileChangeType.ADDED == "added"
        assert FileChangeType.MODIFIED == "modified"
        assert FileChangeType.DELETED == "deleted"


class TestReviewSeverity:
    def test_review_severity_values(self):
        assert ReviewSeverity.CRITICAL == "critical"
        assert ReviewSeverity.WARNING == "warning"
        assert ReviewSeverity.INFO == "info"


class TestVerdict:
    def test_verdict_values(self):
        assert Verdict.APPROVED == "APPROVED"
        assert Verdict.CHANGES_REQUESTED == "CHANGES REQUESTED"
        assert Verdict.CRITICAL_BLOCKER == "CRITICAL BLOCKER"


class TestFileChange:
    def test_file_change_defaults(self):
        fc = FileChange(path="src/main.py")
        assert fc.path == "src/main.py"
        assert fc.language == Language.UNKNOWN
        assert fc.change_type == FileChangeType.MODIFIED
        assert fc.is_test is False
        assert fc.diff is None

    def test_file_change_with_values(self):
        fc = FileChange(
            path="src/test_main.py",
            language=Language.PYTHON,
            change_type=FileChangeType.ADDED,
            is_test=True,
            diff="+new line",
        )
        assert fc.language == Language.PYTHON
        assert fc.change_type == FileChangeType.ADDED
        assert fc.is_test is True
        assert fc.diff == "+new line"


class TestReviewIssue:
    def test_review_issue_minimal(self):
        issue = ReviewIssue(file="test.py", severity=ReviewSeverity.WARNING, message="Bad style")
        assert issue.file == "test.py"
        assert issue.line is None
        assert issue.severity == ReviewSeverity.WARNING
        assert issue.message == "Bad style"
        assert issue.suggestion is None
        assert issue.rule is None

    def test_review_issue_full(self):
        issue = ReviewIssue(
            file="test.py",
            line=42,
            severity=ReviewSeverity.CRITICAL,
            message="Type error",
            suggestion="Add type hint",
            rule="mypy-error",
        )
        assert issue.line == 42
        assert issue.suggestion == "Add type hint"
        assert issue.rule == "mypy-error"


class TestReviewResult:
    def test_review_result_defaults(self):
        rr = ReviewResult(language=Language.PYTHON)
        assert rr.language == Language.PYTHON
        assert rr.issues == []
        assert rr.summary == ""
        assert rr.passed is True
        assert rr.tool_output is None

    def test_review_result_with_issues(self):
        issues = [
            ReviewIssue(file="a.py", severity=ReviewSeverity.WARNING, message="Issue 1"),
            ReviewIssue(file="b.py", severity=ReviewSeverity.CRITICAL, message="Issue 2"),
        ]
        rr = ReviewResult(
            language=Language.PYTHON,
            issues=issues,
            summary="Found 2 issues",
            passed=False,
        )
        assert len(rr.issues) == 2
        assert rr.passed is False


class TestTestResult:
    def test_test_result_defaults(self):
        tr = TestResult(framework="pytest")
        assert tr.framework == "pytest"
        assert tr.total == 0
        assert tr.passed == 0
        assert tr.failed == 0
        assert tr.skipped == 0
        assert tr.coverage is None
        assert tr.coverage_threshold is None
        assert tr.coverage_passed is None
        assert tr.failures == []

    def test_test_result_evaluate_pass(self):
        tr = TestResult(framework="pytest", total=100, passed=100, coverage=85.0)
        tr.evaluate(threshold=80.0)
        assert tr.coverage_threshold == 80.0
        assert tr.coverage_passed is True

    def test_test_result_evaluate_fail(self):
        tr = TestResult(framework="pytest", total=100, passed=70, coverage=70.0)
        tr.evaluate(threshold=80.0)
        assert tr.coverage_threshold == 80.0
        assert tr.coverage_passed is False

    def test_test_result_evaluate_no_coverage(self):
        tr = TestResult(framework="pytest", total=10, passed=10)
        tr.evaluate(threshold=80.0)
        assert tr.coverage_threshold is None
        assert tr.coverage_passed is None


class TestComparisonResult:
    def test_comparison_result_defaults(self):
        cr = ComparisonResult()
        assert cr.previous_review_id is None
        assert cr.new_issues == []
        assert cr.fixed_issues == []
        assert cr.remaining_issues == []
        assert cr.trend == "new_review"

    def test_comparison_result_with_values(self):
        cr = ComparisonResult(
            previous_review_id="review-1",
            trend="improving",
            new_issues=[ReviewIssue(file="a.py", severity=ReviewSeverity.INFO, message="New")],
            fixed_issues=[ReviewIssue(file="b.py", severity=ReviewSeverity.WARNING, message="Fixed")],
        )
        assert cr.previous_review_id == "review-1"
        assert cr.trend == "improving"
        assert len(cr.new_issues) == 1
        assert len(cr.fixed_issues) == 1


class TestPRMetadata:
    def test_pr_metadata(self):
        pm = PRMetadata(
            project_key="TEST",
            repo_slug="test-repo",
            pr_id="123",
            title="Test PR",
            author="testuser",
        )
        assert pm.project_key == "TEST"
        assert pm.repo_slug == "test-repo"
        assert pm.pr_id == "123"
        assert pm.title == "Test PR"
        assert pm.author == "testuser"
        assert pm.description == ""
        assert pm.source_branch == ""
        assert pm.destination_branch == ""


class TestNodeHealth:
    def test_node_health(self):
        nh = NodeHealth(
            node_name="fetch_pr",
            status="success",
            duration_ms=123.45,
        )
        assert nh.node_name == "fetch_pr"
        assert nh.status == "success"
        assert nh.duration_ms == 123.45
        assert nh.error_message is None
        assert nh.retry_count == 0
        assert nh.timestamp is not None

    def test_node_health_with_error(self):
        nh = NodeHealth(
            node_name="review_java",
            status="error",
            duration_ms=500.0,
            error_message="Timeout",
            retry_count=3,
        )
        assert nh.status == "error"
        assert nh.error_message == "Timeout"
        assert nh.retry_count == 3


class TestReviewQuality:
    def test_review_quality_defaults(self):
        rq = ReviewQuality(review_id="r1", pr_id="p1", language="python")
        assert rq.review_id == "r1"
        assert rq.pr_id == "p1"
        assert rq.language == "python"
        assert rq.issues_suggested == 0
        assert rq.issues_accepted == 0
        assert rq.issues_dismissed == 0
        assert rq.accuracy_score == 0.0

    def test_review_quality_calculate_accuracy(self):
        rq = ReviewQuality(
            review_id="r1",
            pr_id="p1",
            language="python",
            issues_suggested=10,
            issues_accepted=8,
            issues_dismissed=2,
        )
        rq.calculate_accuracy()
        assert rq.accuracy_score == 0.8

    def test_review_quality_calculate_accuracy_no_issues(self):
        rq = ReviewQuality(review_id="r1", pr_id="p1", language="python")
        rq.calculate_accuracy()
        assert rq.accuracy_score == 0.0