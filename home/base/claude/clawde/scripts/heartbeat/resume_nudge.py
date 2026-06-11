import argparse
import subprocess
import sys
import time

from tmux import (
    capture_recent_pane,
    find_tmux_socket,
    pane_indicates_resume_confirmation_modal,
    pane_is_at_claude_repl_prompt,
    send_prompt_via_tmux_buffer,
    send_single_key_to_pane,
    wait_for_claude_prompt,
)

AGENT_WRAPPER_COMMAND_FRAGMENT = "agent-wrapper/wrapper.py --agent-name"
LIVE_CLAUDE_PROCESS_NAME_FRAGMENT = "claude"
LIVE_CLAUDE_WAIT_MAX_ATTEMPTS = 20
LIVE_CLAUDE_WAIT_DELAY_SECONDS = 2
RESUME_MODAL_DISMISS_MAX_ATTEMPTS = 15
RESUME_MODAL_DISMISS_DELAY_SECONDS = 2
RESUME_MODAL_SUMMARY_RESUME_KEY = "Enter"

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


def find_agent_wrapper_process_id(agent_name: str) -> int | None:
    completed_process = subprocess.run(
        ["pgrep", "-f", f"{AGENT_WRAPPER_COMMAND_FRAGMENT} {agent_name}"],
        capture_output=True,
        text=True,
    )
    for line in completed_process.stdout.split():
        if line.strip().isdigit():
            return int(line)
    return None


def agent_wrapper_has_live_claude_child(wrapper_process_id: int) -> bool:
    completed_process = subprocess.run(
        ["pgrep", "-P", str(wrapper_process_id), "-l"],
        capture_output=True,
        text=True,
    )
    return any(
        LIVE_CLAUDE_PROCESS_NAME_FRAGMENT in child_description
        for child_description in completed_process.stdout.splitlines()
        if child_description.strip()
    )


def agent_has_live_claude_repl(agent_name: str) -> bool:
    wrapper_process_id = find_agent_wrapper_process_id(agent_name)
    if wrapper_process_id is None:
        return False
    return agent_wrapper_has_live_claude_child(wrapper_process_id)


def wait_for_live_claude_repl(agent_name: str) -> bool:
    for _ in range(LIVE_CLAUDE_WAIT_MAX_ATTEMPTS):
        if agent_has_live_claude_repl(agent_name):
            return True
        time.sleep(LIVE_CLAUDE_WAIT_DELAY_SECONDS)
    return False


def dismiss_resume_confirmation_modal_if_present(tmux_socket: str, target: str) -> None:
    for _ in range(RESUME_MODAL_DISMISS_MAX_ATTEMPTS):
        pane_content = capture_recent_pane(tmux_socket, target)
        if pane_content is None:
            time.sleep(RESUME_MODAL_DISMISS_DELAY_SECONDS)
            continue
        if pane_is_at_claude_repl_prompt(pane_content):
            return
        if pane_indicates_resume_confirmation_modal(pane_content):
            send_single_key_to_pane(
                tmux_socket, target, RESUME_MODAL_SUMMARY_RESUME_KEY
            )
            return
        time.sleep(RESUME_MODAL_DISMISS_DELAY_SECONDS)


def main() -> None:
    arguments = parse_arguments()
    target = f"{arguments.session}:{arguments.window}"

    if not wait_for_live_claude_repl(arguments.window):
        print(
            f"Agent {target} has no live claude REPL (dormant or outside active "
            "hours); skipping resume nudge.",
            file=sys.stderr,
        )
        return

    tmux_socket = find_tmux_socket()
    if not tmux_socket:
        print("Error: no tmux socket found", file=sys.stderr)
        sys.exit(1)

    dismiss_resume_confirmation_modal_if_present(tmux_socket, target)

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
