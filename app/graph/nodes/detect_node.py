from app.graph.nodes.detect_languages import detect_languages_from_files
from app.graph.state import PRReviewState


async def detect_node(state: PRReviewState) -> dict[str, list[str]]:
    files_changed = state.get("files_changed") or ""
    file_paths = [line.split(" (")[0] for line in files_changed.split("\n") if line.strip()]
    files = detect_languages_from_files(file_paths)
    languages = list({f.language.value for f in files})
    return {"languages": languages}
