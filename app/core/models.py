from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Language(str, Enum):
    JAVA = "java"
    PYTHON = "python"
    CPP = "cpp"
    ADA = "ada"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


class FileChangeType(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class ReviewSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Verdict(str, Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES REQUESTED"
    CRITICAL_BLOCKER = "CRITICAL BLOCKER"


class FileChange(BaseModel):
    path: str
    language: Language = Language.UNKNOWN
    change_type: FileChangeType = FileChangeType.MODIFIED
    is_test: bool = False
    diff: Optional[str] = None


class ReviewIssue(BaseModel):
    file: str
    line: Optional[int] = None
    severity: ReviewSeverity
    message: str
    suggestion: Optional[str] = None
    rule: Optional[str] = None


class ReviewResult(BaseModel):
    language: Language
    issues: List[ReviewIssue] = Field(default_factory=list)
    summary: str = ""
    passed: bool = True
    tool_output: Optional[str] = None


class TestResult(BaseModel):
    framework: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage: Optional[float] = None
    coverage_threshold: Optional[float] = None
    coverage_passed: Optional[bool] = None
    failures: List[Dict[str, Any]] = Field(default_factory=list)

    def evaluate(self, threshold: float) -> None:
        if self.coverage is not None:
            self.coverage_threshold = threshold
            self.coverage_passed = self.coverage >= threshold


class ComparisonResult(BaseModel):
    previous_review_id: Optional[str] = None
    new_issues: List[ReviewIssue] = Field(default_factory=list)
    fixed_issues: List[ReviewIssue] = Field(default_factory=list)
    remaining_issues: List[ReviewIssue] = Field(default_factory=list)
    trend: str = "new_review"


class PRMetadata(BaseModel):
    project_key: str
    repo_slug: str
    pr_id: str
    title: str = ""
    author: str = ""
    description: str = ""
    source_branch: str = ""
    destination_branch: str = ""


class NodeHealth(BaseModel):
    node_name: str
    status: str
    duration_ms: float
    error_message: Optional[str] = None
    retry_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReviewSummary(BaseModel):
    review_id: str
    pr_id: str
    project_key: str
    repo_slug: str
    author: str = ""
    languages: List[str] = Field(default_factory=list)
    verdict: Optional[str] = None
    duration_ms: float = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewQuality(BaseModel):
    review_id: str
    pr_id: str
    language: str
    issues_suggested: int = 0
    issues_accepted: int = 0
    issues_dismissed: int = 0
    accuracy_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def calculate_accuracy(self) -> None:
        total = self.issues_accepted + self.issues_dismissed
        if total > 0:
            self.accuracy_score = self.issues_accepted / total
        else:
            self.accuracy_score = 0.0