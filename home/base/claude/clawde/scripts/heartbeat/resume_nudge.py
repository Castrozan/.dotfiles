import argparse
import sys

from tmux import (
    find_tmux_socket,
    send_prompt_via_tmux_buffer,
    wait_for_claude_prompt,
)

RESUME_NUDGE_PROMPT = (
    "<resume>\n"
    "You were just restarted to apply a deployment; your previous session and full "
    "context were preserved via claude --continue. Resume whatever task you had in "
    "flight from exactly where you left off, and tell the user you are back if a "
    "reply was pending. Do not re-run steps that already completed, and never trigger "
    "another rebuild or redeploy as a result of this message. If you had no task in "
    "progress, simply end your turn - idle is the correct outcome.\n"
    "</resume>\n"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clawde-resume-nudge",
        description="After a warm redeploy, wait for a clawde agent's REPL to come "
        "back and inject a one-shot prompt so the resumed agent continues its "
        "in-flight work instead of idling at the prompt.",
    )
    parser.add_argument("--session", required=True, help="tmux session name")
    parser.add_argument("--window", required=True, help="tmux window name (agent name)")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    target = f"{arguments.session}:{arguments.window}"

    tmux_socket = find_tmux_socket()
    if not tmux_socket:
        print("Error: no tmux socket found", file=sys.stderr)
        sys.exit(1)

    if not wait_for_claude_prompt(tmux_socket, target):
        print(
            f"Error: claude REPL prompt not detected for {target} after waiting; "
            "not injecting resume nudge.",
            file=sys.stderr,
        )
        sys.exit(1)

    send_prompt_via_tmux_buffer(tmux_socket, target, RESUME_NUDGE_PROMPT)


if __name__ == "__main__":
    main()
