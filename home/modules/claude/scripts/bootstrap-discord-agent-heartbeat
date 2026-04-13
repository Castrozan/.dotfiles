import argparse
import os
import subprocess
import sys
import tempfile
import time

MAX_WAIT_ATTEMPTS = 90
INITIAL_DELAY_SECONDS = 30
ONBOARDING_INDICATORS = [
    "Select login method",
    "Choose the text style",
    "Paste code here",
    "Claude account with subscription",
]


def find_tmux_socket() -> str | None:
    tmux_tmpdir = os.environ.get("TMUX_TMPDIR")
    uid = os.getuid()
    candidate_directories = []
    if tmux_tmpdir:
        candidate_directories.append(tmux_tmpdir)
    candidate_directories.extend(
        [
            f"/run/user/{uid}/tmux-{uid}",
            f"/tmp/tmux-{uid}",
        ]
    )
    for directory in candidate_directories:
        if os.path.exists(directory):
            socket_path = os.path.join(directory, "default")
            if os.path.exists(socket_path):
                return socket_path
    return None


def run_tmux_command(tmux_socket: str, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-S", tmux_socket, *arguments],
        capture_output=True,
        text=True,
    )


def pane_is_at_onboarding(pane_content: str) -> bool:
    return any(indicator in pane_content for indicator in ONBOARDING_INDICATORS)


def pane_is_at_claude_repl_prompt(pane_content: str) -> bool:
    if pane_is_at_onboarding(pane_content):
        return False
    for line in pane_content.splitlines():
        stripped = line.strip()
        if stripped == "❯" or stripped.endswith(" ❯"):
            return True
    return False


def wait_for_claude_prompt(tmux_socket: str, target: str) -> bool:
    print(f"Waiting {INITIAL_DELAY_SECONDS}s for onboarding to complete...")
    time.sleep(INITIAL_DELAY_SECONDS)

    for attempt in range(MAX_WAIT_ATTEMPTS):
        result = run_tmux_command(
            tmux_socket,
            "capture-pane",
            "-t",
            target,
            "-p",
            "-S",
            "-10",
        )
        if result.returncode == 0:
            content = result.stdout
            if pane_is_at_onboarding(content):
                print(f"  Attempt {attempt + 1}: still at onboarding, waiting...")
                time.sleep(5)
                continue
            if pane_is_at_claude_repl_prompt(content):
                return True
        time.sleep(2)
    return False


def send_bootstrap_via_tmux_buffer(tmux_socket: str, target: str, content: str) -> bool:
    buffer_name = "heartbeat-bootstrap"

    with tempfile.NamedTemporaryFile(
        mode="w",
        prefix="heartbeat-bootstrap-",
        suffix=".md",
        delete=False,
    ) as temporary_file:
        temporary_file.write(content)
        temporary_file_path = temporary_file.name

    try:
        load_result = run_tmux_command(
            tmux_socket, "load-buffer", "-b", buffer_name, temporary_file_path
        )
        if load_result.returncode != 0:
            print(
                f"Error loading buffer: {load_result.stderr.strip()}",
                file=sys.stderr,
            )
            return False

        paste_result = run_tmux_command(
            tmux_socket, "paste-buffer", "-b", buffer_name, "-t", target
        )
        if paste_result.returncode != 0:
            print(
                f"Error pasting buffer: {paste_result.stderr.strip()}",
                file=sys.stderr,
            )
            return False

        run_tmux_command(tmux_socket, "send-keys", "-t", target, "Enter")
        run_tmux_command(tmux_socket, "delete-buffer", "-b", buffer_name)
        return True
    finally:
        os.unlink(temporary_file_path)


def build_heartbeat_bootstrap_prompt(
    heartbeat_interval: str, heartbeat_prompt: str
) -> str:
    return (
        "You are a persistent autonomous agent with a heartbeat loop. "
        "Set up your heartbeat now: use CronCreate with "
        f'cron: "{heartbeat_interval}", recurring: true, '
        "and this prompt:\n\n"
        f'"{heartbeat_prompt}"\n\n'
        "Then read HEARTBEAT.md in your workspace. "
        "If it contains only 'No active work', this is your first session - "
        "initialize your state per your skill instructions. "
        "Otherwise, resume from the state on disk."
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bootstrap-discord-agent-heartbeat",
        description="Send a heartbeat bootstrap prompt to a discord agent running in tmux",
    )
    parser.add_argument(
        "--session",
        required=True,
        help="tmux session name",
    )
    parser.add_argument(
        "--window",
        required=True,
        help="tmux window name (agent name)",
    )
    parser.add_argument(
        "--interval",
        required=True,
        help="Cron expression for heartbeat interval",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt to send on each heartbeat tick",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    tmux_socket = find_tmux_socket()
    if not tmux_socket:
        print("Error: no tmux socket found", file=sys.stderr)
        sys.exit(1)

    target = f"{args.session}:{args.window}"
    print(f"Waiting for claude prompt in {target}...")

    if not wait_for_claude_prompt(tmux_socket, target):
        print(
            "Error: claude REPL prompt not detected after waiting. "
            "Agent may be stuck at onboarding. Skipping bootstrap.",
            file=sys.stderr,
        )
        sys.exit(1)

    bootstrap_content = build_heartbeat_bootstrap_prompt(args.interval, args.prompt)

    if send_bootstrap_via_tmux_buffer(tmux_socket, target, bootstrap_content):
        print(f"Heartbeat bootstrap sent to {target}")
    else:
        print(f"Failed to send heartbeat bootstrap to {target}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
