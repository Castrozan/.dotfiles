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
    return _status_for_captured_runs(return_code, output, revision)


def _status_for_captured_runs(return_code: int, output: str, revision: str) -> dict:
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
        latest = _latest_runs_for_revision(runs, revision)
        pending = _pending_runs(latest)
        failing = _failing_runs(latest)
        failed_workflows = _failed_workflow_details(failing)
    except (ValueError, TypeError, KeyError):
        return {"available": True, "state": "pending", "parse_error": True}
    state = _state_for_workflows(failing, pending, latest)
    return {
        "available": True,
        "state": state,
        "revision": revision,
        "workflows_checked": len(latest),
        "failing": failed_workflows,
        "pending": [run["workflowName"] for run in pending],
    }


def _state_for_workflows(failing: list, pending: list, latest: dict) -> str:
    return "failing" if failing else "pending" if pending or not latest else "passing"


def _latest_runs_for_revision(runs: list, revision: str) -> dict:
    latest = {}
    for run in runs:
        if run["headSha"] == revision:
            latest.setdefault(run["workflowName"], run)
    return latest


def _pending_runs(latest: dict) -> list:
    return [run for run in latest.values() if run["status"] != "completed"]


def _failing_runs(latest: dict) -> list:
    return [
        run
        for run in latest.values()
        if run["status"] == "completed" and run["conclusion"] != "success"
    ]


def _failed_workflow_details(failing: list) -> list[dict]:
    return [{"workflow": run["workflowName"], "url": run["url"]} for run in failing]
