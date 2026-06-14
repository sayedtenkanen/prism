import pytest

from app.sia.dataset import DatasetBuilder, DatasetEntry
from app.sia.feedback import FeedbackAction, FeedbackCollector, FindingFeedback
from app.sia.memory import MemoryEntry, MemoryStore


class TestDatasetEntry:
    def test_creation(self):
        entry = DatasetEntry(
            entry_id="entry-1",
            files_changed="app.py",
            diff="+new line",
            expected_findings=[{"finding": "x"}],
            languages=["python"],
        )
        assert entry.entry_id == "entry-1"
        assert entry.languages == ["python"]
        assert len(entry.expected_findings) == 1

    def test_default_values(self):
        entry = DatasetEntry(entry_id="e-1", files_changed="a.py", diff="+x")
        assert entry.expected_findings == []
        assert entry.languages == []


class TestDatasetBuilder:
    def test_init(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)
        assert builder.memory_store is memory
        assert builder.feedback_collector is feedback

    def test_build_from_memory_empty(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)
        dataset = builder.build_from_memory()
        assert dataset == []

    def test_build_from_memory_with_feedback(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        entry = MemoryEntry(
            pr_id="pr-1",
            repo="org/repo",
            findings=[{"finding": "x", "severity": "high"}],
            languages=["python"],
        )
        memory.add(entry)

        fb = FindingFeedback(finding_id="x", action=FeedbackAction.ACCEPT)
        feedback.submit(fb)

        dataset = builder.build_from_memory()
        assert len(dataset) == 1
        assert len(dataset[0].expected_findings) == 1

    def test_build_from_memory_finding_id_collision(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        entry = MemoryEntry(
            pr_id="pr-1",
            repo="org/repo",
            findings=[
                {"severity": "high"},
                {"severity": "low"},
            ],
            languages=["python"],
        )
        memory.add(entry)

        fb = FindingFeedback(finding_id="", action=FeedbackAction.ACCEPT)
        feedback.submit(fb)

        dataset = builder.build_from_memory()
        assert len(dataset) == 0

    def test_build_from_memory_finding_id_no_collision(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        entry = MemoryEntry(
            pr_id="pr-1",
            repo="org/repo",
            findings=[
                {"finding_id": "f-1", "severity": "high"},
                {"finding_id": "f-2", "severity": "low"},
            ],
            languages=["python"],
        )
        memory.add(entry)

        fb1 = FindingFeedback(finding_id="f-1", action=FeedbackAction.ACCEPT)
        feedback.submit(fb1)

        dataset = builder.build_from_memory()
        assert len(dataset) == 1
        assert len(dataset[0].expected_findings) == 1

    def test_build_from_memory_min_feedback(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        entry = MemoryEntry(
            pr_id="pr-1",
            repo="org/repo",
            findings=[{"finding": "x"}],
            languages=["python"],
        )
        memory.add(entry)

        fb = FindingFeedback(finding_id="x", action=FeedbackAction.ACCEPT)
        feedback.submit(fb)

        dataset = builder.build_from_memory(min_feedback=2)
        assert len(dataset) == 0

    def test_build_from_memory_custom_limit(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        for i in range(5):
            entry = MemoryEntry(
                pr_id=f"pr-{i}",
                repo="org/repo",
                findings=[{"finding": f"x-{i}"}],
                languages=["python"],
            )
            memory.add(entry)
            fb = FindingFeedback(finding_id=f"x-{i}", action=FeedbackAction.ACCEPT)
            feedback.submit(fb)

        dataset = builder.build_from_memory(limit=2)
        assert len(dataset) == 2

    def test_build_from_memory_with_only_non_accept_feedback(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        entry = MemoryEntry(
            pr_id="pr-1",
            repo="org/repo",
            findings=[{"finding": "x", "severity": "high"}],
            languages=["python"],
        )
        memory.add(entry)

        fb_reject = FindingFeedback(finding_id="x", action=FeedbackAction.REJECT)
        feedback.submit(fb_reject)

        dataset = builder.build_from_memory()
        assert dataset == []

    def test_build_from_memory_filter_by_repo(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        memory.add(MemoryEntry(pr_id="pr-1", repo="org/repo-a", findings=[{"finding": "x"}]))
        memory.add(MemoryEntry(pr_id="pr-2", repo="org/repo-b", findings=[{"finding": "y"}]))

        fb_a = FindingFeedback(finding_id="x", action=FeedbackAction.ACCEPT)
        fb_b = FindingFeedback(finding_id="y", action=FeedbackAction.ACCEPT)
        feedback.submit(fb_a)
        feedback.submit(fb_b)

        dataset = builder.build_from_memory(repo="org/repo-a")
        assert len(dataset) == 1
        assert dataset[0].metadata["repo"] == "org/repo-a"

    def test_build_from_memory_filter_by_language(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        memory.add(MemoryEntry(pr_id="pr-1", repo="org/repo", languages=["python"], findings=[{"finding": "x"}]))
        memory.add(MemoryEntry(pr_id="pr-2", repo="org/repo", languages=["java"], findings=[{"finding": "y"}]))

        feedback.submit(FindingFeedback(finding_id="x", action=FeedbackAction.ACCEPT))
        feedback.submit(FindingFeedback(finding_id="y", action=FeedbackAction.ACCEPT))

        dataset = builder.build_from_memory(language="python")
        assert len(dataset) == 1

    def test_build_from_findings(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        findings = [
            {"finding": "x", "severity": "high"},
            {"finding": "y", "severity": "low"},
        ]
        entry = builder.build_from_findings(
            pr_id="pr-1",
            repo="org/repo",
            files_changed="app.py",
            diff="+new line",
            findings=findings,
            accepted_indices=[0],
        )
        assert entry.entry_id == "pr-1"
        assert len(entry.expected_findings) == 1
        assert entry.expected_findings[0]["finding"] == "x"

    def test_build_from_findings_invalid_indices(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        findings = [
            {"finding": "x", "severity": "high"},
            {"finding": "y", "severity": "low"},
        ]
        with pytest.raises(ValueError, match="Invalid indices"):
            builder.build_from_findings(
                pr_id="pr-1",
                repo="org/repo",
                files_changed="app.py",
                diff="+new line",
                findings=findings,
                accepted_indices=[0, 5],
            )

    def test_export_and_import_json(self, tmp_path):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        dataset = [
            DatasetEntry(entry_id="e-1", files_changed="a.py", diff="+x", languages=["python"]),
            DatasetEntry(entry_id="e-2", files_changed="b.py", diff="+y", languages=["java"]),
        ]

        path = tmp_path / "dataset.json"
        builder.export_json(dataset, path)
        loaded = builder.import_json(path)
        assert len(loaded) == 2
        assert loaded[0].entry_id == "e-1"

    def test_export_and_import_json_utf8(self, tmp_path):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        dataset = [
            DatasetEntry(
                entry_id="e-1",
                files_changed="a.py",
                diff="+ new code with unicode: café, naïve, résumé",
                languages=["python"],
            ),
        ]

        path = tmp_path / "dataset_utf8.json"
        builder.export_json(dataset, path)
        loaded = builder.import_json(path)
        assert len(loaded) == 1
        assert loaded[0].diff == "+ new code with unicode: café, naïve, résumé"

    def test_import_json_nonexistent(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        with pytest.raises(FileNotFoundError):
            builder.import_json("/nonexistent/path.json")

    def test_filter_entries_by_language(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        dataset = [
            DatasetEntry(entry_id="e-1", files_changed="a.py", diff="+x", languages=["python"]),
            DatasetEntry(entry_id="e-2", files_changed="b.py", diff="+y", languages=["java"]),
        ]
        filtered = builder.filter_entries(dataset, min_findings=0, languages=["python"])
        assert len(filtered) == 1

    def test_filter_entries_by_min_findings(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        dataset = [
            DatasetEntry(entry_id="e-1", files_changed="a.py", diff="+x", expected_findings=[{"finding": "x"}]),
            DatasetEntry(entry_id="e-2", files_changed="b.py", diff="+y", expected_findings=[]),
        ]
        filtered = builder.filter_entries(dataset, min_findings=1)
        assert len(filtered) == 1

    def test_get_statistics(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)

        dataset = [
            DatasetEntry(
                entry_id="e-1",
                files_changed="a.py",
                diff="+x",
                languages=["python"],
                expected_findings=[{"finding": "x"}],
            ),
            DatasetEntry(
                entry_id="e-2",
                files_changed="b.py",
                diff="+y",
                languages=["java", "python"],
                expected_findings=[{"finding": "y"}, {"finding": "z"}],
            ),
        ]
        stats = builder.get_statistics(dataset)
        assert stats["total_entries"] == 2
        assert stats["total_findings"] == 3
        assert stats["avg_findings_per_entry"] == 1.5
        assert stats["languages"]["python"] == 2
        assert stats["languages"]["java"] == 1

    def test_get_statistics_empty(self):
        memory = MemoryStore()
        feedback = FeedbackCollector()
        builder = DatasetBuilder(memory, feedback)
        stats = builder.get_statistics([])
        assert stats["total_entries"] == 0
        assert "avg_findings_per_entry" in stats
        assert stats["avg_findings_per_entry"] == 0.0
