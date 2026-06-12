import dspy

from app.agents.signatures import (
    ArchitectureReview,
    DebateChallenge,
    DocumentationReview,
    JudgeAggregation,
    MaintainabilityReview,
    PerformanceReview,
    SecurityReview,
    TestingReview,
)


class TestDSPySignatures:
    def test_security_review_fields(self):
        sig = SecurityReview
        assert "security" in sig.__doc__.lower()
        expected = {"files_changed", "diff", "findings"}
        assert set(sig.fields.keys()) == expected

    def test_performance_review_fields(self):
        sig = PerformanceReview
        assert "performance" in sig.__doc__.lower()
        expected = {"files_changed", "diff", "findings"}
        assert set(sig.fields.keys()) == expected

    def test_maintainability_review_fields(self):
        sig = MaintainabilityReview
        assert "maintainability" in sig.__doc__.lower()
        expected = {"files_changed", "diff", "findings"}
        assert set(sig.fields.keys()) == expected

    def test_testing_review_fields(self):
        sig = TestingReview
        assert "test" in sig.__doc__.lower()
        expected = {"files_changed", "diff", "findings"}
        assert set(sig.fields.keys()) == expected

    def test_architecture_review_fields(self):
        sig = ArchitectureReview
        assert "architectural" in sig.__doc__.lower()
        expected = {"files_changed", "diff", "findings"}
        assert set(sig.fields.keys()) == expected

    def test_documentation_review_fields(self):
        sig = DocumentationReview
        assert "documentation" in sig.__doc__.lower()
        expected = {"files_changed", "diff", "findings"}
        assert set(sig.fields.keys()) == expected

    def test_judge_aggregation_fields(self):
        sig = JudgeAggregation
        assert "aggregate" in sig.__doc__.lower()
        expected = {
            "all_findings",
            "summary",
            "critical_findings",
            "major_findings",
            "minor_findings",
            "approved",
        }
        assert set(sig.fields.keys()) == expected

    def test_debate_challenge_fields(self):
        sig = DebateChallenge
        assert "challenge" in sig.__doc__.lower()
        expected = {
            "finding",
            "challenger_agent",
            "code_context",
            "challenge",
            "confidence_adjustment",
        }
        assert set(sig.fields.keys()) == expected

    def test_all_signatures_are_dspy_signatures(self):
        signatures = [
            SecurityReview,
            PerformanceReview,
            MaintainabilityReview,
            TestingReview,
            ArchitectureReview,
            DocumentationReview,
            JudgeAggregation,
            DebateChallenge,
        ]
        for sig in signatures:
            assert issubclass(sig, dspy.Signature)
