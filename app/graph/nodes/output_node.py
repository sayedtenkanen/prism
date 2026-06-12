import asyncio
import json
from typing import Any


async def output_node(state: dict[str, Any]) -> dict[str, Any]:
    report = {
        "summary": state.get("summary", ""),
        "approved": state.get("approved", False),
        "critical_findings": state.get("critical_findings", []),
        "major_findings": state.get("major_findings", []),
        "minor_findings": state.get("minor_findings", []),
        "debate_records": state.get("debate_records", []),
        "languages": state.get("languages", []),
        "pr_metadata": state.get("pr_metadata"),
    }
    report_path = f"report_{state.get('pr_number', 'unknown')}.json"

    def _write(path: str, payload: dict[str, Any]) -> None:
        with open(path, "w") as f:
            json.dump(payload, f, indent=2, default=str)

    await asyncio.to_thread(_write, report_path, report)
    return {"json_report_path": report_path}
