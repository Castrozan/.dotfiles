#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_HEARTBEAT_INTERVAL = "3,33 * * * *"
DEFAULT_MODEL = "opus"
CLAUDE_INPUT_PROMPT_INDICATOR = "❯"
MAX_WAIT_ATTEMPTS_FOR_CLAUDE_PROMPT = 30


def find_tmux_socket() -> str | None:
    uid = os.getuid()
    candidate_directories = [
        Path(f"/run/user/{uid}/tmux-{uid}"),
        Path(f"/tmp/tmux-{uid}"),
    ]
    for directory in candidate_directories:
        if directory.exists():
            for socket_file in directory.glob("default"):
                if socket_file.is_socket():
                    return str(socket_file)
    return None


def run_tmux_command(tmux_socket: str, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-S", tmux_socket, *arguments],
        capture_output=True,
        text=True,
    )


def resolve_current_tmux_session(tmux_socket: str) -> str | None:
    result = run_tmux_command(tmux_socket, "display-message", "-p", "#S")
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def validate_project_directory(project_directory: Path) -> None:
    if not project_directory.is_dir():
        print(
            f"Error: project directory not found: {project_directory}", file=sys.stderr
        )
        sys.exit(1)

    claude_md = project_directory / "CLAUDE.md"
    if not claude_md.is_file():
        print(
            f"Error: no CLAUDE.md found in {project_directory}"
            " - the agent needs instructions",
            file=sys.stderr,
        )
        sys.exit(1)


def ensure_heartbeat_file_exists(project_directory: Path) -> None:
    heartbeat_file = project_directory / "HEARTBEAT.md"
    if not heartbeat_file.exists():
        heartbeat_file.write_text("# Heartbeat\n\nNo active work.\n")
        print(f"Created {heartbeat_file}")


def check_tmux_window_already_exists(
    tmux_socket: str, tmux_session: str, window_name: str
) -> bool:
    result = run_tmux_command(
        tmux_socket, "list-windows", "-t", tmux_session, "-F", "#{window_name}"
    )
    if result.returncode != 0:
        return False
    existing_windows = result.stdout.strip().splitlines()
    return window_name in existing_windows


def create_tmux_window(
    tmux_socket: str, tmux_session: str, window_name: str, working_directory: Path
) -> None:
    if check_tmux_window_already_exists(tmux_socket, tmux_session, window_name):
        print(
            f"Error: tmux window '{window_name}' already exists"
            f" in session '{tmux_session}'",
            file=sys.stderr,
        )
        print(
            f"Attach with: tmux attach -t {tmux_session}:{window_name}", file=sys.stderr
        )
        sys.exit(1)

    result = run_tmux_command(
        tmux_socket,
        "new-window",
        "-t",
        tmux_session,
        "-n",
        window_name,
        "-c",
        str(working_directory),
    )
    if result.returncode != 0:
        print(
            f"Error: failed to create tmux window: {result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)


def send_keys_to_tmux_pane(tmux_socket: str, target: str, keys: str) -> None:
    result = run_tmux_command(
        tmux_socket, "list-panes", "-t", target, "-F", "#{pane_index}"
    )
    pane_index = (
        result.stdout.strip().splitlines()[0] if result.returncode == 0 else "0"
    )
    run_tmux_command(
        tmux_socket, "send-keys", "-t", f"{target}.{pane_index}", keys, "Enter"
    )


def wait_for_claude_input_prompt(tmux_socket: str, target: str) -> None:
    for attempt in range(1, MAX_WAIT_ATTEMPTS_FOR_CLAUDE_PROMPT + 1):
        result = run_tmux_command(
            tmux_socket, "capture-pane", "-t", target, "-p", "-S", "-10"
        )
        if result.returncode == 0 and CLAUDE_INPUT_PROMPT_INDICATOR in result.stdout:
            return
        time.sleep(1)

    max_seconds = MAX_WAIT_ATTEMPTS_FOR_CLAUDE_PROMPT
    print(
        f"Warning: claude input prompt not detected"
        f" after {max_seconds}s, sending bootstrap anyway",
        file=sys.stderr,
    )


def build_bootstrap_prompt(heartbeat_interval: str) -> str:
    heartbeat_tick_prompt = (
        "Heartbeat tick. Read HEARTBEAT.md."
        " If there are pending tasks with elapsed intervals,"
        " work on the highest priority one."
        " If nothing needs attention,"
        " do nothing - do not respond or log."
    )
    return (
        "You are a persistent project agent."
        " Read your CLAUDE.md for your identity and instructions."
        " Read HEARTBEAT.md for pending work.\n\n"
        "Set up your heartbeat loop now:"
        f' use CronCreate with cron: "{heartbeat_interval}",'
        " recurring: true, and this prompt:\n\n"
        f'"{heartbeat_tick_prompt}"\n\n'
        "After setting up the heartbeat,"
        " read HEARTBEAT.md and act on any pending work."
        " If nothing is pending,"
        " report your status and wait for instructions."
    )


def send_bootstrap_prompt(
    tmux_socket: str, target: str, heartbeat_interval: str
) -> None:
    bootstrap_content = build_bootstrap_prompt(heartbeat_interval)

    with tempfile.NamedTemporaryFile(
        mode="w", prefix="project-agent-bootstrap-", suffix=".md", delete=False
    ) as f:
        f.write(bootstrap_content)
        bootstrap_file = f.name

    try:
        wait_for_claude_input_prompt(tmux_socket, target)
        run_tmux_command(tmux_socket, "load-buffer", bootstrap_file)
        run_tmux_command(tmux_socket, "paste-buffer", "-t", target)
        run_tmux_command(tmux_socket, "send-keys", "-t", target, "Enter")
    finally:
        os.unlink(bootstrap_file)


def build_claude_launch_command(model: str, agent_name: str) -> str:
    return f"claude --model {model} --name {agent_name} --dangerously-skip-permissions"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="launch-project-agent",
        description=(
            "Launch a persistent project agent"
            " (Claude Code + heartbeat loop)"
            " in a tmux window."
        ),
    )
    parser.add_argument(
        "project_directory",
        type=Path,
        help="Path to the project. Must contain a CLAUDE.md file.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--name",
        dest="agent_name",
        default=None,
        help="Agent name / tmux window name (default: derived from directory name)",
    )
    parser.add_argument(
        "--heartbeat",
        default=DEFAULT_HEARTBEAT_INTERVAL,
        help=f'Heartbeat cron expression (default: "{DEFAULT_HEARTBEAT_INTERVAL}")',
    )
    parser.add_argument(
        "--session",
        dest="tmux_session",
        default=None,
        help="tmux session to create the window in (default: current session)",
    )
    parser.add_argument(
        "--no-bootstrap", action="store_true", help="Skip sending the bootstrap prompt"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    project_directory = args.project_directory.resolve()
    validate_project_directory(project_directory)
    ensure_heartbeat_file_exists(project_directory)

    agent_name = args.agent_name or project_directory.name

    tmux_socket = find_tmux_socket()
    if not tmux_socket:
        print("Error: no tmux socket found", file=sys.stderr)
        sys.exit(1)

    tmux_session = args.tmux_session
    if not tmux_session:
        tmux_session = resolve_current_tmux_session(tmux_socket)
        if not tmux_session:
            print("Error: not inside tmux and no --session specified", file=sys.stderr)
            sys.exit(1)

    create_tmux_window(tmux_socket, tmux_session, agent_name, project_directory)

    target = f"{tmux_session}:{agent_name}"
    claude_command = build_claude_launch_command(args.model, agent_name)
    send_keys_to_tmux_pane(tmux_socket, target, claude_command)

    if not args.no_bootstrap:
        send_bootstrap_prompt(tmux_socket, target, args.heartbeat)

    print(f"Launched project agent '{agent_name}' in {target}")
    print(f"  Project: {project_directory}")
    print(f"  Model: {args.model}")
    print(f"  Heartbeat: {args.heartbeat}")
    print(f"  Attach: tmux select-window -t {target}")


if __name__ == "__main__":
    main()
