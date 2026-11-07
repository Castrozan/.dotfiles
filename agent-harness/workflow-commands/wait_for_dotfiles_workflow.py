import argparse
import json
import re
import sys
import time
from pathlib import Path

POLL_INTERVAL_SECONDS = 15
MAXIMUM_WAIT_SECONDS = 540
TERMINAL_STATUSES = frozenset({"completed", "failed", "killed"})
RUN_IDENTIFIER_PATTERN = re.compile(r"wf_[a-z0-9-]{6,}")
STILL_RUNNING_MESSAGE = "still running; run this command again"


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dotfiles-workflow-wait",
        description=(
            "Block until a Claude Code workflow run ends and print its result, "
            "keeping a non-interactive lead's turn open while the run works."
        ),
    )
    parser.add_argument("run_identifier", help="the wf_... run ID Workflow returned")
    return parser.parse_args(command_line_arguments)


def terminal_workflow_state(projects_directory: Path, run_identifier: str):
    for state_path in projects_directory.glob(f"*/*/workflows/{run_identifier}.json"):
        try:
            state = json.loads(state_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if state.get("status") in TERMINAL_STATUSES:
            return state
    return None


def wait_for_terminal_state(
    projects_directory: Path,
    run_identifier: str,
    clock=time.monotonic,
    sleep=time.sleep,
):
    deadline = clock() + MAXIMUM_WAIT_SECONDS
    while clock() < deadline:
        state = terminal_workflow_state(projects_directory, run_identifier)
        if state is not None:
            return state
        sleep(POLL_INTERVAL_SECONDS)
    return None


def rendered_outcome(state) -> str:
    if state is None:
        return STILL_RUNNING_MESSAGE
    result = state.get("result")
    rendered_result = result if isinstance(result, str) else json.dumps(result)
    return f"status={state['status']}\n{rendered_result}"


def main() -> int:
    run_identifier = parse_command_line(sys.argv[1:]).run_identifier
    if not RUN_IDENTIFIER_PATTERN.fullmatch(run_identifier):
        raise SystemExit(f"{run_identifier!r} is not a workflow run ID")
    projects_directory = Path.home() / ".claude" / "projects"
    print(rendered_outcome(wait_for_terminal_state(projects_directory, run_identifier)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
