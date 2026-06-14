from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.nodes.detect_node import detect_node
from app.graph.nodes.fetch_pr import fetch_pr
from app.graph.nodes.output_node import output_node
from app.graph.nodes.review_node import review_node
from app.graph.nodes.sia_node import sia_node
from app.graph.state import PRReviewState


def should_continue(state: PRReviewState) -> str:
    if state.get("errors"):
        return "output"
    if state.get("hitl_enabled"):
        return "human_approval"
    return "output"


async def human_approval(state: PRReviewState) -> PRReviewState:
    return state


def build_graph() -> Any:
    graph = StateGraph(PRReviewState)

    graph.add_node("fetch_pr", fetch_pr)
    graph.add_node("detect_languages", detect_node)
    graph.add_node("run_review", review_node)
    graph.add_node("human_approval", human_approval)
    graph.add_node("sia", sia_node)
    graph.add_node("output", output_node)

    graph.set_entry_point("fetch_pr")
    graph.add_edge("fetch_pr", "detect_languages")
    graph.add_edge("detect_languages", "run_review")
    graph.add_conditional_edges("run_review", should_continue, {"output": "sia", "human_approval": "human_approval"})
    graph.add_edge("human_approval", "sia")
    graph.add_edge("sia", "output")
    graph.add_edge("output", END)

    return graph.compile()


_graph: Any = None


def get_graph() -> Any:
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
