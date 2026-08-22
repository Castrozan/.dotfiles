import json
import shlex
import subprocess
import time

from . import restart_lock

RESTART_CONTINUATION_PROMPT = (
    "This session was restarted. Continue from where you left off."
)
DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS = 0.25
RESUMED_HARNESS_TAKEOVER_WAIT_SECONDS = 30.0
RESUMED_HARNESS_INTERFACE_WAIT_SECONDS = 60.0
PANE_OUTPUT_QUIET_SECONDS = 1.5
PANE_POLL_INTERVAL_SECONDS = 0.2


def wait_until(condition, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while not condition():
        if time.monotonic() >= deadline:
            return False
        time.sleep(PANE_POLL_INTERVAL_SECONDS)
    return True


def relaunch_commands_for(
    multiplexer_name: str, pane_identifier: str, resume_command: list[str]
) -> list[list[str]]:
    serialized_resume_command = shlex.join(resume_command)
    if multiplexer_name == "herdr":
        return herdr_agent_send_commands(pane_identifier, serialized_resume_command)
    raise ValueError(f"unsupported multiplexer: {multiplexer_name}")


def herdr_agent_send_commands(pane_identifier: str, text: str) -> list[list[str]]:
    return [
        ["herdr", "agent", "send", pane_identifier, text],
        ["herdr", "pane", "send-keys", pane_identifier, "Enter"],
    ]


def run_text_submission_commands(submission_commands: list[list[str]]) -> None:
    typing_command, enter_command = submission_commands
    subprocess.run(typing_command, check=True)
    time.sleep(DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS)
    subprocess.run(enter_command, check=True)


def relaunch_target_check_command_for(
    multiplexer_name: str, pane_identifier: str
) -> list[str]:
    if multiplexer_name == "herdr":
        return ["herdr", "pane", "process-info", "--pane", pane_identifier]
    raise ValueError(f"unsupported multiplexer: {multiplexer_name}")


def relaunch_target_is_ready(multiplexer_name: str, pane_identifier: str) -> bool:
    try:
        subprocess.run(
            relaunch_target_check_command_for(multiplexer_name, pane_identifier),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def run_relaunch_commands(
    multiplexer_name: str, pane_identifier: str, resume_command: list[str]
) -> None:
    run_text_submission_commands(
        relaunch_commands_for(multiplexer_name, pane_identifier, resume_command)
    )


def wait_for_resumed_harness_to_take_over(pane_identifier: str) -> bool:
    """Typed text only reaches the harness once the harness, rather than the pane's
    shell, is the process reading the terminal."""
    return wait_until(
        lambda: not herdr_pane_is_idle(pane_identifier),
        RESUMED_HARNESS_TAKEOVER_WAIT_SECONDS,
    )


def wait_for_resumed_harness_to_draw_its_interface(pane_identifier: str) -> None:
    """A harness still painting its interface throws typed input away, and herdr's own
    agent report cannot say when that ends: it names the agent from the process the
    moment it starts, keeps the dead agent's status on a released pane, and never
    reports codex as anything but idle. The pane's output going quiet after the first
    repaint is the one readiness signal every harness gives. Best effort, because a
    harness that keeps painting still queues what it is handed."""
    deadline = time.monotonic() + RESUMED_HARNESS_INTERFACE_WAIT_SECONDS
    drawn_screen = herdr_pane_visible_text(pane_identifier)
    repainted_at = None
    while time.monotonic() < deadline:
        time.sleep(PANE_POLL_INTERVAL_SECONDS)
        current_screen = herdr_pane_visible_text(pane_identifier)
        if current_screen != drawn_screen:
            drawn_screen = current_screen
            repainted_at = time.monotonic()
        elif (
            repainted_at is not None
            and time.monotonic() - repainted_at >= PANE_OUTPUT_QUIET_SECONDS
        ):
            return


def continue_resumed_session(pane_identifier: str) -> None:
    run_text_submission_commands(
        herdr_agent_send_commands(pane_identifier, RESTART_CONTINUATION_PROMPT)
    )


def resume_and_continue_session(
    pane_identifier: str, resume_command: list[str]
) -> bool:
    run_relaunch_commands("herdr", pane_identifier, resume_command)
    if not wait_for_resumed_harness_to_take_over(pane_identifier):
        return False
    wait_for_resumed_harness_to_draw_its_interface(pane_identifier)
    continue_resumed_session(pane_identifier)
    return True


def herdr_pane_process_information(pane_identifier: str) -> dict | None:
    try:
        completed_process = subprocess.run(
            ["herdr", "pane", "process-info", "--pane", pane_identifier],
            capture_output=True,
            text=True,
            check=False,
        )
        process_information = json.loads(completed_process.stdout)["result"][
            "process_info"
        ]
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return None
    if completed_process.returncode != 0:
        return None
    return process_information


def herdr_pane_foreground_process_identifiers(
    pane_identifier: str,
) -> set[int] | None:
    process_information = herdr_pane_process_information(pane_identifier)
    if process_information is None:
        return None
    try:
        return {
            process["pid"] for process in process_information["foreground_processes"]
        }
    except (KeyError, TypeError):
        return None


def herdr_pane_visible_text(pane_identifier: str) -> str:
    completed_process = subprocess.run(
        ["herdr", "pane", "read", pane_identifier, "--source", "visible"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed_process.returncode != 0:
        return ""
    return completed_process.stdout


def herdr_pane_is_idle(pane_identifier: str) -> bool:
    process_information = herdr_pane_process_information(pane_identifier)
    if process_information is None:
        return False
    try:
        return (
            process_information["foreground_process_group_id"]
            == process_information["shell_pid"]
        )
    except KeyError:
        return False


def wait_for_relaunch_target_idle(multiplexer_name: str, pane_identifier: str) -> bool:
    if multiplexer_name != "herdr":
        return False
    deadline = time.monotonic() + restart_lock.RESTART_WAIT_SECONDS
    while not herdr_pane_is_idle(pane_identifier):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.2)
    return True
