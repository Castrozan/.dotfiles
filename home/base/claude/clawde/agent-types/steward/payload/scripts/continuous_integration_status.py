"""GitHub Actions status for a pushed revision, for the dotfiles steward agent.

The steward's local `tests/run.sh --nix` gate skips any flake checks the host
system does not expose (on darwin the linux-only `checks.x86_64-linux` set never
runs), so continuous integration on origin/main is the only place the full
cross-system checks execute. That makes it the supreme green gate, and this
module reports its verdict so the steward never rests while it is red or pending.
"""

import json
from collections.abc import Callable
from pathlib import Path

FAILING_CONTINUOUS_INTEGRATION_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "startup_failure",
    "stale",
    "action_required",
}


def continuous_integration_status_for_revision(
    repository: Path,
    revision: str,
    run_capturing: Callable[[list[str], Path, int], tuple[int, str]],
) -> dict:
    if not revision:
        return {"available": True, "state": "none"}
    return_code, output = run_capturing(
        [
            "gh",
            "run",
            "list",
            "--branch",
            "main",
            "--event",
            "push",
            "--limit",
            "40",
            "--json",
            "headSha,status,conclusion,workflowName,url",
        ],
        repository,
        45,
    )
    if return_code == 127:
        return {"available": False}
    if return_code != 0:
        return {"available": True, "query_error": True, "detail": output[:200]}
    try:
        runs = json.loads(output)
    except json.JSONDecodeError:
        return {"available": True, "parse_error": True}

    latest_run_per_workflow: dict[str, dict] = {}
    for run in runs:
        if run.get("headSha") != revision:
            continue
        latest_run_per_workflow.setdefault(run.get("workflowName", "?"), run)

    if not latest_run_per_workflow:
        return {"available": True, "state": "none", "revision": revision}

    pending = [
        run
        for run in latest_run_per_workflow.values()
        if run.get("status") != "completed"
    ]
    failing = [
        run
        for run in latest_run_per_workflow.values()
        if run.get("status") == "completed"
        and run.get("conclusion") in FAILING_CONTINUOUS_INTEGRATION_CONCLUSIONS
    ]

    if failing:
        state = "failing"
    elif pending:
        state = "pending"
    else:
        state = "passing"

    return {
        "available": True,
        "state": state,
        "revision": revision,
        "workflows_checked": len(latest_run_per_workflow),
        "failing": [
            {"workflow": run.get("workflowName", "?"), "url": run.get("url", "")}
            for run in failing
        ],
        "pending": [run.get("workflowName", "?") for run in pending],
    }
