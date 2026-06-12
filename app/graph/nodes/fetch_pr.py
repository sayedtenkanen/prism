from typing import Any

from app.scm.github import GitHubClient


async def fetch_pr(state: dict[str, Any]) -> dict[str, Any]:
    client = GitHubClient(token=state["scm_token"])
    try:
        pr_metadata = await client.get_pr(state["owner"], state["repo"], state["pr_number"])
        diff = await client.get_diff(state["owner"], state["repo"], state["pr_number"])
        files = await client.get_files(state["owner"], state["repo"], state["pr_number"])

        files_changed = "\n".join(
            f"{f.get('filename', '')} ({f.get('language', 'unknown')}) "
            f"[+{f.get('additions', 0)}/-{f.get('deletions', 0)}]"
            for f in files
        )

        return {
            "pr_metadata": pr_metadata,
            "diff": diff,
            "files_changed": files_changed,
        }
    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"fetch_pr: {e}")
        return {"errors": errors}
    finally:
        await client.close()
