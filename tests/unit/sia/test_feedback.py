import pytest

from app.sia.feedback import FeedbackAction, FeedbackCollector, FindingFeedback


class TestFindingFeedback:
    def test_creation(self):
        feedback = FindingFeedback(
            finding_id="finding-1",
            action=FeedbackAction.ACCEPT,
            comment="Looks good",
            reviewer="senior-dev",
        )
        assert feedback.finding_id == "finding-1"
        assert feedback.action == FeedbackAction.ACCEPT
        assert feedback.reviewer == "senior-dev"
        assert feedback.feedback_id

    def test_default_values(self):
        feedback = FindingFeedback(finding_id="f-1", action=FeedbackAction.REJECT)
        assert feedback.comment == ""
        assert feedback.suggested_severity is None
        assert feedback.reviewer == ""


class TestFeedbackCollector:
    def test_init(self):
        collector = FeedbackCollector()
        assert collector.count() == 0

    def test_submit(self):
        collector = FeedbackCollector()
        feedback = FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT)
        collector.submit(feedback)
        assert collector.count() == 1

    def test_get_for_finding(self):
        collector = FeedbackCollector()
        fb1 = FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT)
        fb2 = FindingFeedback(finding_id="f-1", action=FeedbackAction.REJECT)
        fb3 = FindingFeedback(finding_id="f-2", action=FeedbackAction.ACCEPT)
        collector.submit(fb1)
        collector.submit(fb2)
        collector.submit(fb3)
        results = collector.get_for_finding("f-1")
        assert len(results) == 2

    def test_get_by_action(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT))
        collector.submit(FindingFeedback(finding_id="f-2", action=FeedbackAction.REJECT))
        collector.submit(FindingFeedback(finding_id="f-3", action=FeedbackAction.ACCEPT))
        accepted = collector.get_by_action(FeedbackAction.ACCEPT)
        assert len(accepted) == 2

    def test_get_by_reviewer(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT, reviewer="alice"))
        collector.submit(FindingFeedback(finding_id="f-2", action=FeedbackAction.REJECT, reviewer="bob"))
        collector.submit(FindingFeedback(finding_id="f-3", action=FeedbackAction.ACCEPT, reviewer="alice"))
        alice_fb = collector.get_by_reviewer("alice")
        assert len(alice_fb) == 2

    def test_get_recent(self):
        collector = FeedbackCollector()
        for i in range(5):
            collector.submit(FindingFeedback(finding_id=f"f-{i}", action=FeedbackAction.ACCEPT))
        recent = collector.get_recent(limit=3)
        assert len(recent) == 3

    def test_count(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT))
        collector.submit(FindingFeedback(finding_id="f-2", action=FeedbackAction.REJECT))
        assert collector.count() == 2

    def test_get_acceptance_rate(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT))
        collector.submit(FindingFeedback(finding_id="f-2", action=FeedbackAction.ACCEPT))
        collector.submit(FindingFeedback(finding_id="f-3", action=FeedbackAction.REJECT))
        assert collector.get_acceptance_rate() == pytest.approx(0.6667, abs=1e-3)

    def test_get_acceptance_rate_empty(self):
        collector = FeedbackCollector()
        assert collector.get_acceptance_rate() == 0.0

    def test_get_rejection_rate(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT))
        collector.submit(FindingFeedback(finding_id="f-2", action=FeedbackAction.REJECT))
        collector.submit(FindingFeedback(finding_id="f-3", action=FeedbackAction.REJECT))
        assert collector.get_rejection_rate() == pytest.approx(0.6667, abs=1e-3)

    def test_get_rejection_rate_empty(self):
        collector = FeedbackCollector()
        assert collector.get_rejection_rate() == 0.0

    def test_get_summary(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT, reviewer="alice"))
        collector.submit(FindingFeedback(finding_id="f-2", action=FeedbackAction.REJECT, reviewer="bob"))
        summary = collector.get_summary()
        assert summary["total_feedback"] == 2
        assert summary["by_action"]["accept"] == 1
        assert summary["by_action"]["reject"] == 1
        assert summary["by_reviewer"]["alice"] == 1
        assert summary["by_reviewer"]["bob"] == 1

    def test_get_summary_unnamed_reviewers(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT, reviewer="alice"))
        collector.submit(FindingFeedback(finding_id="f-2", action=FeedbackAction.REJECT))
        collector.submit(FindingFeedback(finding_id="f-3", action=FeedbackAction.MODIFY))
        summary = collector.get_summary()
        assert summary["total_feedback"] == 3
        assert summary["by_reviewer"]["alice"] == 1
        assert "" not in summary["by_reviewer"]
        assert summary["unnamed_reviewer_count"] == 2

    def test_clear(self):
        collector = FeedbackCollector()
        collector.submit(FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT))
        collector.clear()
        assert collector.count() == 0
