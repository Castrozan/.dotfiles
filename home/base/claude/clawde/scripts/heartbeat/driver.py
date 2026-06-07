import argparse
import datetime
import subprocess
import sys
import time

from cron import cron_expression_matches, seconds_until_next_minute_boundary
from tmux import (
    find_tmux_socket,
    pane_is_idle,
    send_prompt_via_tmux_buffer,
    wait_for_claude_prompt,
)

GATE_TIMEOUT_SECONDS = 120


def gate_allows_wake(gate_command: str | None) -> bool:
    if not gate_command:
        return True
    try:
        result = subprocess.run(
            ["bash", "-c", gate_command],
            capture_output=True,
            text=True,
            timeout=GATE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def drive_heartbeat(
    tmux_socket: str,
    target: str,
    cron_expression: str,
    prompt: str,
    gate_command: str | None,
) -> None:
    while True:
        time.sleep(seconds_until_next_minute_boundary(datetime.datetime.now()))
        now = datetime.datetime.now()
        if not cron_expression_matches(cron_expression, now):
            continue
        if not pane_is_idle(tmux_socket, target):
            continue
        if not gate_allows_wake(gate_command):
            continue
        send_prompt_via_tmux_buffer(tmux_socket, target, prompt)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clawde-heartbeat-driver",
        description="Drive a clawde agent's heartbeat from outside the LLM: on each "
        "cron-matched minute run an optional deterministic gate and paste the "
        "heartbeat prompt into the agent pane only when the gate allows it.",
    )
    parser.add_argument("--session", required=True, help="tmux session name")
    parser.add_argument("--window", required=True, help="tmux window name (agent name)")
    parser.add_argument(
        "--interval", required=True, help="Cron expression for heartbeat interval"
    )
    parser.add_argument(
        "--prompt", required=True, help="Prompt pasted into the pane on each fired tick"
    )
    parser.add_argument(
        "--gate-command",
        default=None,
        help="Shell command run before each tick; exit 0 fires the tick, non-zero skips it",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    tmux_socket = find_tmux_socket()
    if not tmux_socket:
        print("Error: no tmux socket found", file=sys.stderr)
        sys.exit(1)

    target = f"{args.session}:{args.window}"

    if not wait_for_claude_prompt(tmux_socket, target):
        print(
            "Error: claude REPL prompt not detected after waiting. "
            "Agent may be stuck at onboarding. Not driving heartbeat.",
            file=sys.stderr,
        )
        sys.exit(1)

    drive_heartbeat(tmux_socket, target, args.interval, args.prompt, args.gate_command)


if __name__ == "__main__":
    main()
