import asyncio
from typing import Any

from app.agents.modules import FullReviewPipeline
from app.graph.state import PRReviewState

_pipeline: FullReviewPipeline | None = None


def get_pipeline() -> FullReviewPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FullReviewPipeline()
    return _pipeline


async def review_node(state: PRReviewState) -> dict[str, Any]:
    files_changed = state.get("files_changed", "")
    diff = state.get("diff", "")
    pipeline = get_pipeline()
    result = await asyncio.to_thread(pipeline, files_changed=files_changed, diff=diff)
    return {
        "agent_results": result.get("agent_results", {}),
        "debate_records": result.get("debate_records", []),
        "summary": result.get("summary", ""),
        "critical_findings": result.get("critical_findings", []),
        "major_findings": result.get("major_findings", []),
        "minor_findings": result.get("minor_findings", []),
        "approved": result.get("approved", False),
    }
