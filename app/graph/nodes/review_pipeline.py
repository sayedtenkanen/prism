from typing import Any

from app.agents.modules import FullReviewPipeline

_pipeline: FullReviewPipeline | None = None


def get_pipeline() -> FullReviewPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FullReviewPipeline()
    return _pipeline


async def run_review_pipeline(state: dict[str, Any]) -> dict[str, Any]:
    files_changed = state.get("files_changed", "")
    diff = state.get("diff", "")
    pipeline = get_pipeline()
    result = pipeline(files_changed=files_changed, diff=diff)
    return {
        "review_summary": result.get("summary", ""),
        "critical_findings": result.get("critical_findings", []),
        "major_findings": result.get("major_findings", []),
        "minor_findings": result.get("minor_findings", []),
        "approved": result.get("approved", False),
        "debate_records": result.get("debate_records", []),
    }
