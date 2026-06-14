import logging
from typing import Any

from app.graph.state import PRReviewState
from app.sia.feedback import FeedbackAction, FeedbackCollector, FindingFeedback
from app.sia.memory import MemoryEntry, MemoryStore

logger = logging.getLogger(__name__)

_memory_store = MemoryStore(max_entries=1000)
_feedback_collector = FeedbackCollector()


def get_memory_store() -> MemoryStore:
    return _memory_store


def get_feedback_collector() -> FeedbackCollector:
    return _feedback_collector


def store_review_in_memory(state: PRReviewState) -> dict[str, Any]:
    owner = state.get("owner", "")
    repo = state.get("repo", "")
    pr_number = state.get("pr_number", 0)
    pr_id = f"{owner}/{repo}#{pr_number}"

    all_findings = []
    all_findings.extend(state.get("critical_findings", []))
    all_findings.extend(state.get("major_findings", []))
    all_findings.extend(state.get("minor_findings", []))

    entry = MemoryEntry(
        pr_id=pr_id,
        repo=f"{owner}/{repo}",
        findings=all_findings,
        verdict="approved" if state.get("approved") else "changes_requested",
        summary=state.get("summary") or "",
        languages=state.get("languages") or [],
        metadata={
            "files_changed": state.get("files_changed") or "",
            "diff": state.get("diff") or "",
            "llm_model": state.get("llm_model") or "",
        },
    )

    _memory_store.add(entry)
    logger.info(f"Stored review in memory: {pr_id} (entry_id={entry.entry_id})")

    return {"memory_entry_id": entry.entry_id}


def collect_feedback(state: PRReviewState) -> dict[str, Any]:
    pr_id = f"{state.get('owner', '')}/{state.get('repo', '')}#{state.get('pr_number', 0)}"

    all_findings = []
    all_findings.extend(state.get("critical_findings", []))
    all_findings.extend(state.get("major_findings", []))
    all_findings.extend(state.get("minor_findings", []))

    feedback_count = 0
    for finding in all_findings:
        finding_id = finding.get("finding_id") or finding.get("finding", "")
        if not finding_id:
            continue

        feedback = FindingFeedback(
            finding_id=finding_id,
            action=FeedbackAction.ACCEPT,
            comment="Auto-accepted: included in approved review",
            reviewer="system",
        )
        _feedback_collector.submit(feedback)
        feedback_count += 1

    logger.info(f"Collected feedback for {pr_id}: {feedback_count} findings")
    return {"feedback_submitted": feedback_count > 0}


async def sia_node(state: PRReviewState) -> dict[str, Any]:
    result: dict[str, Any] = {}

    memory_result = store_review_in_memory(state)
    result.update(memory_result)

    feedback_result = collect_feedback(state)
    result.update(feedback_result)

    return result
