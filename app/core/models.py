from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union

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


# ── Agent-specific finding models ──

FindingSeverity = Literal["critical", "high", "medium", "low", "info"]


class BaseFinding(BaseModel):
    """Base model for all agent-specific findings."""

    finding: str
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    recommendation: str
    file: Optional[str] = None
    line: Optional[int] = None


class SecurityFinding(BaseFinding):
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


class PerformanceFinding(BaseFinding):
    category: Optional[str] = None  # n_plus_one, memory, network, database, loop


class MaintainabilityFinding(BaseFinding):
    complexity_score: Optional[float] = None


class TestingFinding(BaseFinding):
    coverage_gap: Optional[str] = None


class ArchitectureFinding(BaseFinding):
    layer_violation: Optional[str] = None


class DocumentationFinding(BaseFinding):
    pass


Finding = Union[
    SecurityFinding,
    PerformanceFinding,
    MaintainabilityFinding,
    TestingFinding,
    ArchitectureFinding,
    DocumentationFinding,
]


# ── Agent review model ──


class AgentReview(BaseModel):
    agent_name: str
    findings: list[Finding] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    files_analyzed: list[str] = Field(default_factory=list)
    duration_ms: float = 0


# ── Debate models ──


class DebateRecord(BaseModel):
    original_finding: Finding
    challenged_by: str
    challenge_text: str
    revised_finding: Optional[Finding] = None
    confidence_change: float = 0.0
    accepted: bool = True


# ── Judge verdict ──


class JudgeVerdict(BaseModel):
    summary: str
    critical_findings: list[Finding] = Field(default_factory=list)
    major_findings: list[Finding] = Field(default_factory=list)
    minor_findings: list[Finding] = Field(default_factory=list)
    approved: bool = True
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    debate_records: list[DebateRecord] = Field(default_factory=list)


# ── Legacy models (kept for backward compatibility) ──


class ReviewResult(BaseModel):
    language: Language
    issues: list[ReviewIssue] = Field(default_factory=list)
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
    failures: list[dict[str, Any]] = Field(default_factory=list)

    def evaluate(self, threshold: float) -> None:
        if self.coverage is not None:
            self.coverage_threshold = threshold
            self.coverage_passed = self.coverage >= threshold


class ComparisonResult(BaseModel):
    previous_review_id: Optional[str] = None
    new_issues: list[ReviewIssue] = Field(default_factory=list)
    fixed_issues: list[ReviewIssue] = Field(default_factory=list)
    remaining_issues: list[ReviewIssue] = Field(default_factory=list)
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
    provider: str = "github"


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
    languages: list[str] = Field(default_factory=list)
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
