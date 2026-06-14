from app.sia.memory import MemoryEntry, MemoryStore


class TestMemoryEntry:
    def test_creation(self):
        entry = MemoryEntry(
            pr_id="pr-123",
            repo="org/repo",
            findings=[{"finding": "x"}],
            verdict="APPROVED",
            languages=["python"],
        )
        assert entry.pr_id == "pr-123"
        assert entry.repo == "org/repo"
        assert len(entry.findings) == 1
        assert entry.entry_id

    def test_default_values(self):
        entry = MemoryEntry(pr_id="pr-1", repo="org/repo")
        assert entry.findings == []
        assert entry.verdict == ""
        assert entry.languages == []


class TestMemoryStore:
    def test_init(self):
        store = MemoryStore()
        assert store.count() == 0
        assert store.max_entries == 1000

    def test_init_custom_max(self):
        store = MemoryStore(max_entries=100)
        assert store.max_entries == 100

    def test_add_and_get(self):
        store = MemoryStore()
        entry = MemoryEntry(pr_id="pr-1", repo="org/repo")
        store.add(entry)
        result = store.get(entry.entry_id)
        assert result is not None
        assert result.pr_id == "pr-1"

    def test_get_nonexistent(self):
        store = MemoryStore()
        result = store.get("nonexistent")
        assert result is None

    def test_get_by_pr(self):
        store = MemoryStore()
        entry1 = MemoryEntry(pr_id="pr-1", repo="org/repo")
        entry2 = MemoryEntry(pr_id="pr-1", repo="org/repo")
        entry3 = MemoryEntry(pr_id="pr-2", repo="org/repo")
        store.add(entry1)
        store.add(entry2)
        store.add(entry3)
        results = store.get_by_pr("pr-1")
        assert len(results) == 2

    def test_get_by_repo(self):
        store = MemoryStore()
        entry1 = MemoryEntry(pr_id="pr-1", repo="org/repo-a")
        entry2 = MemoryEntry(pr_id="pr-2", repo="org/repo-b")
        entry3 = MemoryEntry(pr_id="pr-3", repo="org/repo-a")
        store.add(entry1)
        store.add(entry2)
        store.add(entry3)
        results = store.get_by_repo("org/repo-a")
        assert len(results) == 2

    def test_get_by_repo_limit(self):
        store = MemoryStore()
        for i in range(10):
            store.add(MemoryEntry(pr_id=f"pr-{i}", repo="org/repo"))
        results = store.get_by_repo("org/repo", limit=3)
        assert len(results) == 3

    def test_search_by_language(self):
        store = MemoryStore()
        store.add(MemoryEntry(pr_id="pr-1", repo="org/repo", languages=["python", "java"]))
        store.add(MemoryEntry(pr_id="pr-2", repo="org/repo", languages=["java"]))
        store.add(MemoryEntry(pr_id="pr-3", repo="org/repo", languages=["python"]))
        results = store.search_by_language("python")
        assert len(results) == 2

    def test_get_recent(self):
        store = MemoryStore()
        for i in range(5):
            store.add(MemoryEntry(pr_id=f"pr-{i}", repo="org/repo"))
        results = store.get_recent(limit=3)
        assert len(results) == 3

    def test_count(self):
        store = MemoryStore()
        store.add(MemoryEntry(pr_id="pr-1", repo="org/repo"))
        store.add(MemoryEntry(pr_id="pr-2", repo="org/repo"))
        assert store.count() == 2

    def test_delete(self):
        store = MemoryStore()
        entry = MemoryEntry(pr_id="pr-1", repo="org/repo")
        store.add(entry)
        assert store.delete(entry.entry_id) is True
        assert store.get(entry.entry_id) is None
        assert store.count() == 0

    def test_delete_nonexistent(self):
        store = MemoryStore()
        assert store.delete("nonexistent") is False

    def test_clear(self):
        store = MemoryStore()
        store.add(MemoryEntry(pr_id="pr-1", repo="org/repo"))
        store.add(MemoryEntry(pr_id="pr-2", repo="org/repo"))
        store.clear()
        assert store.count() == 0

    def test_eviction(self):
        store = MemoryStore(max_entries=3)
        for i in range(5):
            store.add(MemoryEntry(pr_id=f"pr-{i}", repo="org/repo"))
        assert store.count() == 3

    def test_get_summary(self):
        store = MemoryStore()
        store.add(MemoryEntry(pr_id="pr-1", repo="org/repo-a", languages=["python"]))
        store.add(MemoryEntry(pr_id="pr-2", repo="org/repo-b", languages=["java", "python"]))
        summary = store.get_summary()
        assert summary["total_entries"] == 2
        assert summary["unique_repos"] == 2
        assert summary["languages"]["python"] == 2
        assert summary["languages"]["java"] == 1

    def test_repo_and_pr_index_isolation(self):
        store = MemoryStore()
        entry_a = MemoryEntry(pr_id="shared-id", repo="org/repo-x")
        entry_b = MemoryEntry(pr_id="pr-other", repo="shared-id")
        store.add(entry_a)
        store.add(entry_b)

        by_repo = store.get_by_repo("shared-id")
        by_pr = store.get_by_pr("shared-id")

        assert len(by_repo) == 1
        assert by_repo[0].entry_id == entry_b.entry_id
        assert len(by_pr) == 1
        assert by_pr[0].entry_id == entry_a.entry_id
