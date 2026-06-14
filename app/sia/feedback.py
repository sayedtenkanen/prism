from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FeedbackAction(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    MODIFY = "modify"


class FindingFeedback(BaseModel):
    feedback_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    finding_id: str
    action: FeedbackAction
    comment: str = ""
    suggested_severity: str | None = None
    suggested_fix: str | None = None
    timestamp: float = Field(default_factory=time.time)
    reviewer: str = ""


class FeedbackCollector:
    def __init__(self) -> None:
        self._feedback: list[FindingFeedback] = []
        self._index: dict[str, list[int]] = {}

    def submit(self, feedback: FindingFeedback) -> None:
        self._feedback.append(feedback)
        idx = len(self._feedback) - 1
        self._index.setdefault(feedback.finding_id, []).append(idx)

    def get_for_finding(self, finding_id: str) -> list[FindingFeedback]:
        indices = self._index.get(finding_id, [])
        return [self._feedback[i] for i in indices if i < len(self._feedback)]

    def get_by_action(self, action: FeedbackAction, limit: int = 100) -> list[FindingFeedback]:
        results = [f for f in self._feedback if f.action == action]
        return results[-limit:]

    def get_by_reviewer(self, reviewer: str, limit: int = 100) -> list[FindingFeedback]:
        results = [f for f in self._feedback if f.reviewer == reviewer]
        return results[-limit:]

    def get_recent(self, limit: int = 100) -> list[FindingFeedback]:
        return list(self._feedback[-limit:])

    def count(self) -> int:
        return len(self._feedback)

    def get_acceptance_rate(self) -> float:
        if not self._feedback:
            return 0.0
        accepted = sum(1 for f in self._feedback if f.action == FeedbackAction.ACCEPT)
        return round(accepted / len(self._feedback), 4)

    def get_rejection_rate(self) -> float:
        if not self._feedback:
            return 0.0
        rejected = sum(1 for f in self._feedback if f.action == FeedbackAction.REJECT)
        return round(rejected / len(self._feedback), 4)

    def get_summary(self) -> dict[str, Any]:
        by_action: dict[str, int] = {}
        by_reviewer: dict[str, int] = {}
        unnamed_count = 0
        for f in self._feedback:
            by_action[f.action.value] = by_action.get(f.action.value, 0) + 1
            if f.reviewer:
                by_reviewer[f.reviewer] = by_reviewer.get(f.reviewer, 0) + 1
            else:
                unnamed_count += 1

        return {
            "total_feedback": len(self._feedback),
            "by_action": by_action,
            "by_reviewer": by_reviewer,
            "unnamed_reviewer_count": unnamed_count,
            "acceptance_rate": self.get_acceptance_rate(),
            "rejection_rate": self.get_rejection_rate(),
        }

    def clear(self) -> None:
        self._feedback.clear()
        self._index.clear()
