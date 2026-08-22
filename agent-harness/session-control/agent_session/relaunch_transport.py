import json
import shlex
import subprocess
import time

from . import restart_lock

RESTART_CONTINUATION_PROMPT = (
    "This session was restarted. Continue from where you left off."
)
RESTART_CONTINUATION_WAIT_TIMEOUT_MILLISECONDS = 60_000
DELAY_BETWEEN_TYPING_INPUT_AND_PRESSING_ENTER_SECONDS = 0.25


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


def wait_for_resumed_agent_to_be_idle(pane_identifier: str) -> bool:
    completed_process = subprocess.run(
        [
            "herdr",
            "agent",
            "wait",
            pane_identifier,
            "--status",
            "idle",
            "--timeout",
            str(RESTART_CONTINUATION_WAIT_TIMEOUT_MILLISECONDS),
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed_process.returncode == 0


def continue_resumed_session(pane_identifier: str) -> None:
    run_text_submission_commands(
        herdr_agent_send_commands(pane_identifier, RESTART_CONTINUATION_PROMPT)
    )


def resume_and_continue_session(
    pane_identifier: str, resume_command: list[str]
) -> bool:
    run_relaunch_commands("herdr", pane_identifier, resume_command)
    if not wait_for_resumed_agent_to_be_idle(pane_identifier):
        return False
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
