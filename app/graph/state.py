from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from app.core.models import (
    ComparisonResult,
    FileChange,
    Language,
    PRMetadata,
    ReviewResult,
    ReviewSummary,
    TestResult,
)


class PRReviewState(TypedDict, total=False):
    """The shared data package passed from node to node in the LangGraph."""

    # ── Input ──
    project_key: str
    repo_slug: str
    pr_id: str
    hitl_enabled: bool

    # ── Bitbucket Config (injected) ──
    bb_url: str
    bb_token: str

    # ── LLM Config (injected) ──
    llm_provider: str
    llm_model: str
    llm_api_key: str
    llm_temperature: float

    # ── Fetched PR Data ──
    pr_metadata: Optional[PRMetadata]
    diff: Optional[str]
    files: List[FileChange]

    # ── Detection ──
    languages: List[Language]

    # ── Review Results ──
    review_results: Dict[str, ReviewResult]
    test_results: Optional[TestResult]

    # ── Cross-check ──
    doc_code_alignment: Optional[str]

    # ── Comparison ──
    previous_review: Optional[ReviewResult]
    comparison: Optional[ComparisonResult]

    # ── Judge Output ──
    summary: Optional[str]
    verdict: Optional[str]

    # ── Output ──
    bb_comment_url: Optional[str]
    json_report_path: Optional[str]
    review_summary: Optional[ReviewSummary]

    # ── Error tracking ──
    errors: List[str]
    retry_counts: Dict[str, int]


def create_initial_state(
    project_key: str,
    repo_slug: str,
    pr_id: str,
    bb_url: str,
    bb_token: str,
    llm_api_key: str,
    hitl_enabled: bool = True,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
    llm_temperature: float = 0.3,
) -> PRReviewState:
    """Create an initial state for the PR review graph."""
    return PRReviewState(
        project_key=project_key,
        repo_slug=repo_slug,
        pr_id=pr_id,
        hitl_enabled=hitl_enabled,
        bb_url=bb_url,
        bb_token=bb_token,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        llm_temperature=llm_temperature,
        pr_metadata=None,
        diff=None,
        files=[],
        languages=[],
        review_results={},
        test_results=None,
        doc_code_alignment=None,
        previous_review=None,
        comparison=None,
        summary=None,
        verdict=None,
        bb_comment_url=None,
        json_report_path=None,
        review_summary=None,
        errors=[],
        retry_counts={},
    )