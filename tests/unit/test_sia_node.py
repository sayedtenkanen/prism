import pytest

from app.graph.nodes.sia_node import (
    collect_feedback,
    get_feedback_collector,
    get_memory_store,
    store_review_in_memory,
)
from app.graph.state import create_initial_state
from app.sia.feedback import FeedbackAction
from app.sia.memory import MemoryStore


def test_get_memory_store() -> None:
    store = get_memory_store()
    assert isinstance(store, MemoryStore)


def test_get_feedback_collector() -> None:
    from app.sia.feedback import FeedbackCollector

    collector = get_feedback_collector()
    assert isinstance(collector, FeedbackCollector)


def test_store_review_in_memory() -> None:
    state = create_initial_state(
        owner="test",
        repo="repo",
        pr_number=1,
        scm_token="token",
    )
    state["critical_findings"] = [{"finding": "test finding", "severity": "critical"}]
    state["major_findings"] = []
    state["minor_findings"] = []
    state["approved"] = True
    state["summary"] = "Test summary"
    state["languages"] = ["python"]

    result = store_review_in_memory(state)

    assert "memory_entry_id" in result
    assert result["memory_entry_id"] is not None

    store = get_memory_store()
    assert store.count() > 0


def test_collect_feedback() -> None:
    state = create_initial_state(
        owner="test",
        repo="repo",
        pr_number=2,
        scm_token="token",
    )
    state["critical_findings"] = [{"finding": "test finding", "severity": "critical"}]
    state["major_findings"] = []
    state["minor_findings"] = []

    result = collect_feedback(state)

    assert result["feedback_submitted"] is True

    collector = get_feedback_collector()
    assert collector.count() > 0


def test_store_review_empty_findings() -> None:
    state = create_initial_state(
        owner="test",
        repo="repo",
        pr_number=3,
        scm_token="token",
    )
    state["critical_findings"] = []
    state["major_findings"] = []
    state["minor_findings"] = []

    result = store_review_in_memory(state)

    assert "memory_entry_id" in result
    assert result["memory_entry_id"] is not None
