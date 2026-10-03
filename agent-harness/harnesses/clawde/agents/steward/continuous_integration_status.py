import json
from pathlib import Path
from collections.abc import Callable


def continuous_integration_status_for_revision(
    repository: Path,
    revision: str,
    run_capturing: Callable[[list[str], Path, int], tuple[int, str]],
) -> dict:
    if not revision:
        return {"available": True, "state": "none"}
    return_code, output = run_capturing(
        ["git-forge", "--commit", revision], repository, 45
    )
    if return_code != 0:
        return {
            "available": return_code != 127,
            "state": "pending",
            "query_error": True,
            "detail": output[:200],
        }
    try:
        runs = json.loads(output)
        if not isinstance(runs, list):
            raise ValueError("Expected a list of CI runs")
        latest = {}
        for run in runs:
            if run["headSha"] == revision:
                latest.setdefault(run["workflowName"], run)
        pending = [run for run in latest.values() if run["status"] != "completed"]
        failing = [
            run
            for run in latest.values()
            if run["status"] == "completed" and run["conclusion"] != "success"
        ]
        failed_workflows = [
            {"workflow": run["workflowName"], "url": run["url"]} for run in failing
        ]
    except (ValueError, TypeError, KeyError):
        return {"available": True, "state": "pending", "parse_error": True}
    state = "failing" if failing else "pending" if pending or not latest else "passing"
    return {
        "available": True,
        "state": state,
        "revision": revision,
        "workflows_checked": len(latest),
        "failing": failed_workflows,
        "pending": [run["workflowName"] for run in pending],
    }
