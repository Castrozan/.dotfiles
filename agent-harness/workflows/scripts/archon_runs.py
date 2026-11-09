import json
import subprocess
from pathlib import Path

WAIT_COMMAND_NAME = "dotfiles-workflow-wait"
MAXIMUM_WAIT_SECONDS = 540
TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})


def run_archon_json(
    archon_arguments: list[str], working_directory: Path | None = None
) -> dict:
    completed = subprocess.run(
        archon_arguments,
        cwd=working_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        reply = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise SystemExit(
            completed.stderr.strip()
            or completed.stdout.strip()
            or "archon returned no output"
        )
    if not reply.get("ok", True):
        raise SystemExit(reply.get("error", "archon refused the request"))
    return reply


def wait_for_run(run_identifier: str) -> None:
    subprocess.run(
        [
            "archon",
            "workflow",
            "wait",
            run_identifier,
            "--json",
            "--timeout",
            str(MAXIMUM_WAIT_SECONDS),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def rendered_returns(terminal_record: dict) -> str:
    returned_value = (terminal_record.get("returns") or {}).get("value")
    if returned_value is None:
        return terminal_record.get("error") or "the workflow returned no result"
    return (
        returned_value
        if isinstance(returned_value, str)
        else json.dumps(returned_value, indent=2)
    )


def rendered_outcome(run_identifier: str, run_record: dict) -> str:
    status = run_record.get("status", "unknown")
    if status not in TERMINAL_STATUSES:
        return (
            f"status={status}: still running; run {WAIT_COMMAND_NAME} "
            f"{run_identifier} again"
        )
    return (
        f"status={status}\n{rendered_returns(run_record.get('terminal_record') or {})}"
    )


def report_run(run_identifier: str) -> str:
    wait_for_run(run_identifier)
    run_record = run_archon_json(
        ["archon", "workflow", "get", run_identifier, "--json"]
    )
    return rendered_outcome(run_identifier, run_record)
