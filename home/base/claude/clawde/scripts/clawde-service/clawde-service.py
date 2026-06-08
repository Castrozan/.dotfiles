import argparse
import json
import subprocess
import sys
import time

import agent_wrapper_reconcile

BOOTSTRAP_PLACEHOLDER_WINDOW_NAME = "__bootstrap__"
SUPERVISOR_POLL_INTERVAL_SECONDS = 10
AGENT_STARTUP_STAGGER_SECONDS = 2


def run_tmux_command(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def session_exists(session_name: str) -> bool:
    return run_tmux_command("has-session", "-t", session_name).returncode == 0


def window_exists(session_name: str, window_name: str) -> bool:
    result = run_tmux_command(
        "list-windows", "-t", session_name, "-F", "#{window_name}"
    )
    if result.returncode != 0:
        return False
    return window_name in result.stdout.splitlines()


def create_session_with_placeholder_window(session_name: str) -> None:
    result = run_tmux_command(
        "new-session",
        "-d",
        "-s",
        session_name,
        "-n",
        BOOTSTRAP_PLACEHOLDER_WINDOW_NAME,
        "sleep infinity",
    )
    if result.returncode != 0:
        print(
            f"Error: failed to create tmux session {session_name!r}: {result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)


def remove_placeholder_window(session_name: str) -> None:
    run_tmux_command(
        "kill-window", "-t", f"{session_name}:{BOOTSTRAP_PLACEHOLDER_WINDOW_NAME}"
    )


def ensure_agent_window(
    session_name: str, window_name: str, wrapper_command: str
) -> bool:
    if window_exists(session_name, window_name):
        return False
    result = run_tmux_command(
        "new-window", "-t", session_name, "-n", window_name, wrapper_command
    )
    if result.returncode != 0:
        print(
            f"Error: failed to create tmux window {window_name!r}: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    return True


def ensure_agent_windows_for_session(session_specification: dict) -> None:
    session_name = session_specification["name"]

    placeholder_created = False
    if not session_exists(session_name):
        create_session_with_placeholder_window(session_name)
        placeholder_created = True

    declared_agent_names = {
        agent_specification["name"]
        for agent_specification in session_specification["agents"]
    }
    agent_names_with_a_running_wrapper = (
        agent_wrapper_reconcile.agent_names_with_running_wrapper_after_reconcile(
            session_name, declared_agent_names
        )
    )

    for agent_specification in session_specification["agents"]:
        if agent_specification["name"] in agent_names_with_a_running_wrapper:
            continue
        agent_window_was_created = ensure_agent_window(
            session_name,
            agent_specification["name"],
            agent_specification["wrapper_command"],
        )
        if agent_window_was_created:
            time.sleep(AGENT_STARTUP_STAGGER_SECONDS)

    if placeholder_created:
        remove_placeholder_window(session_name)


def ensure_all_agent_windows(specification: dict) -> None:
    for session_specification in specification["sessions"]:
        ensure_agent_windows_for_session(session_specification)


def reconcile_sessions_forever(
    specification: dict,
    poll_interval_seconds: int = SUPERVISOR_POLL_INTERVAL_SECONDS,
) -> None:
    while True:
        ensure_all_agent_windows(specification)
        time.sleep(poll_interval_seconds)


def load_specification(specification_file_path: str) -> dict:
    with open(specification_file_path) as specification_file:
        return json.load(specification_file)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clawde-service",
        description=(
            "Idempotently ensure every declared clawde tmux session and all agent "
            "windows exist, then reconcile forever so any session or window that "
            "dies after startup gets recreated on the next poll."
        ),
    )
    parser.add_argument(
        "--specification-file",
        required=True,
        help="Path to JSON file describing the sessions and their agents",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    specification = load_specification(arguments.specification_file)
    reconcile_sessions_forever(specification)


if __name__ == "__main__":
    main()
