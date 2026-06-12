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
    def test_security_review_signature(self):
        sig = SecurityReview
        assert "security" in sig.__doc__.lower()
        fields = sig.fields
        assert "files_changed" in fields
        assert "diff" in fields
        assert "findings" in fields

    def test_performance_review_signature(self):
        sig = PerformanceReview
        assert "performance" in sig.__doc__.lower()
        fields = sig.fields
        assert "files_changed" in fields
        assert "diff" in fields
        assert "findings" in fields

    def test_maintainability_review_signature(self):
        sig = MaintainabilityReview
        assert "maintainability" in sig.__doc__.lower()
        fields = sig.fields
        assert "files_changed" in fields
        assert "diff" in fields
        assert "findings" in fields

    def test_testing_review_signature(self):
        sig = TestingReview
        assert "test" in sig.__doc__.lower()
        fields = sig.fields
        assert "files_changed" in fields
        assert "diff" in fields
        assert "findings" in fields

    def test_architecture_review_signature(self):
        sig = ArchitectureReview
        assert "architectural" in sig.__doc__.lower()
        fields = sig.fields
        assert "files_changed" in fields
        assert "diff" in fields
        assert "findings" in fields

    def test_documentation_review_signature(self):
        sig = DocumentationReview
        assert "documentation" in sig.__doc__.lower()
        fields = sig.fields
        assert "files_changed" in fields
        assert "diff" in fields
        assert "findings" in fields

    def test_judge_aggregation_signature(self):
        sig = JudgeAggregation
        assert "aggregate" in sig.__doc__.lower()
        fields = sig.fields
        assert "all_findings" in fields
        assert "summary" in fields
        assert "critical_findings" in fields
        assert "major_findings" in fields
        assert "minor_findings" in fields
        assert "approved" in fields

    def test_debate_challenge_signature(self):
        sig = DebateChallenge
        assert "challenge" in sig.__doc__.lower()
        fields = sig.fields
        assert "finding" in fields
        assert "challenger_agent" in fields
        assert "code_context" in fields
        assert "challenge" in fields
        assert "confidence_adjustment" in fields

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
