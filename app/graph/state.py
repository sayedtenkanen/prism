from typing import Any, Optional

from typing_extensions import TypedDict


class PRReviewState(TypedDict, total=False):
    # ── Input ──
    owner: str
    repo: str
    pr_number: int
    scm_token: str
    scm_provider: str
    hitl_enabled: bool

    # ── LLM Config ──
    llm_model: str
    llm_api_key: str

    # ── Fetched PR Data ──
    pr_metadata: Optional[dict[str, Any]]
    diff: Optional[str]
    files_changed: Optional[str]

    # ── Detection ──
    languages: list[str]

    # ── DSPy Review Results ──
    agent_results: Optional[dict[str, Any]]
    debate_records: list[dict[str, Any]]

    # ── Judge Verdict ──
    summary: Optional[str]
    critical_findings: list[dict[str, Any]]
    major_findings: list[dict[str, Any]]
    minor_findings: list[dict[str, Any]]
    approved: bool

    # ── Output ──
    review_url: Optional[str]
    json_report_path: Optional[str]

    # ── Error tracking ──
    errors: list[str]
    retry_counts: dict[str, int]


def create_initial_state(
    owner: str,
    repo: str,
    pr_number: int,
    scm_token: str,
    scm_provider: str = "github",
    hitl_enabled: bool = True,
    llm_model: str = "gpt-4o",
    llm_api_key: str = "",
) -> PRReviewState:
    return PRReviewState(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        scm_token=scm_token,
        scm_provider=scm_provider,
        hitl_enabled=hitl_enabled,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        pr_metadata=None,
        diff=None,
        files_changed=None,
        languages=[],
        agent_results=None,
        debate_records=[],
        summary=None,
        critical_findings=[],
        major_findings=[],
        minor_findings=[],
        approved=False,
        review_url=None,
        json_report_path=None,
        errors=[],
        retry_counts={},
    )
