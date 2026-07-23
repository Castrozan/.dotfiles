import time

from e2e_herdr import run_herdr_command

AGENT_START_WORKING_TIMEOUT_SECONDS = 30
INPUT_SETTLE_SECONDS = 2
FULL_SCROLLBACK_LINE_BUDGET = 5000


def wait_for_agent_status(
    pane_id: str, agent_status: str, timeout_seconds: float
) -> bool:
    completed = run_herdr_command(
        [
            "wait",
            "agent-status",
            pane_id,
            "--status",
            agent_status,
            "--timeout",
            str(int(timeout_seconds * 1000)),
        ],
        timeout_seconds=timeout_seconds + 10,
    )
    return completed.returncode == 0


def wait_for_claude_to_become_ready(pane_id: str, timeout_seconds: float = 90) -> bool:
    if not wait_for_agent_status(pane_id, "idle", timeout_seconds):
        return False
    time.sleep(INPUT_SETTLE_SECONDS)
    return True


def send_prompt_to_claude_session(pane_id: str, prompt_text: str) -> bool:
    collapsed_prompt = " ".join(prompt_text.strip().split())
    typed = run_herdr_command(["pane", "send-text", pane_id, collapsed_prompt])
    if typed.returncode != 0:
        return False
    return run_herdr_command(["pane", "send-keys", pane_id, "Enter"]).returncode == 0


def wait_for_response_completion(pane_id: str, timeout_seconds: float = 300) -> bool:
    if not wait_for_agent_status(
        pane_id, "working", AGENT_START_WORKING_TIMEOUT_SECONDS
    ):
        return False
    return wait_for_agent_status(pane_id, "idle", timeout_seconds)


def capture_full_terminal_output(pane_id: str) -> str:
    completed = run_herdr_command(
        [
            "pane",
            "read",
            pane_id,
            "--source",
            "recent-unwrapped",
            "--lines",
            str(FULL_SCROLLBACK_LINE_BUDGET),
        ],
        timeout_seconds=30,
    )
    return completed.stdout
