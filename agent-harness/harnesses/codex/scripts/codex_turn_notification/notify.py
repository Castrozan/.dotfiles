import json
import subprocess
import sys
from pathlib import Path

from focus import handle_notification_action


NOTIFICATION_TITLE_CHARACTER_LIMIT = 100
NOTIFICATION_BODY_CHARACTER_LIMIT = 320
NOTIFICATION_TITLE_PREFIX = "Codex · "
NOTIFICATION_PROCESS_TIMEOUT_SECONDS = 3610


def normalize_text(value: object) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def bound_text(value: str, character_limit: int) -> str:
    if len(value) <= character_limit:
        return value
    return value[: character_limit - 1].rstrip() + "…"


def request_text(event: dict[str, object]) -> str:
    input_messages = event.get("input-messages")
    if isinstance(input_messages, list):
        for input_message in reversed(input_messages):
            normalized_input_message = normalize_text(input_message)
            if normalized_input_message:
                return normalized_input_message
    return Path.cwd().name or "Codex"


def notification_text(event: dict[str, object]) -> tuple[str, str]:
    title_text_limit = NOTIFICATION_TITLE_CHARACTER_LIMIT - len(
        NOTIFICATION_TITLE_PREFIX
    )
    title = NOTIFICATION_TITLE_PREFIX + bound_text(
        request_text(event), title_text_limit
    )
    body = normalize_text(event.get("last-assistant-message")) or "Turn complete"
    return title, bound_text(body, NOTIFICATION_BODY_CHARACTER_LIMIT)


def linux_notification_arguments(
    notification_executable_path: str, event: dict[str, object]
) -> list[str]:
    title, body = notification_text(event)
    return [
        notification_executable_path,
        "--app-name",
        "Codex",
        "--action=default=Focus session",
        "--wait",
        title,
        body,
    ]


def darwin_notification_arguments(
    notification_executable_path: str,
    event: dict[str, object],
) -> list[str]:
    title, body = notification_text(event)
    arguments = [
        notification_executable_path,
        "--title",
        title,
        "--message",
        body,
        "--actions",
        "Focus session",
        "--close-label",
        "Dismiss",
        "--timeout",
        "3600",
    ]
    thread_identifier = normalize_text(event.get("thread-id"))
    if thread_identifier:
        arguments.extend(["--group", thread_identifier])
    return arguments


def notification_arguments(
    platform: str,
    notification_executable_path: str,
    event: dict[str, object],
) -> list[str]:
    if platform == "linux":
        return linux_notification_arguments(notification_executable_path, event)
    if platform == "darwin":
        return darwin_notification_arguments(
            notification_executable_path,
            event,
        )
    return []


def send_notification(
    platform: str,
    notification_executable_path: str,
    desktop_focus_path: str,
    herdr_path: str,
    event: dict[str, object],
) -> None:
    command_arguments = notification_arguments(
        platform,
        notification_executable_path,
        event,
    )
    if not command_arguments:
        return
    try:
        result = subprocess.run(
            command_arguments,
            capture_output=True,
            text=True,
            check=False,
            timeout=NOTIFICATION_PROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return
    handle_notification_action(
        result.stdout.strip(),
        platform,
        desktop_focus_path,
        herdr_path,
        normalize_text(event.get("thread-id")),
    )


def main(arguments: list[str]) -> int:
    if len(arguments) != 5:
        return 0
    (
        platform,
        notification_executable_path,
        desktop_focus_path,
        herdr_path,
        serialized_event,
    ) = arguments
    try:
        event = json.loads(serialized_event)
    except json.JSONDecodeError:
        return 0
    if not isinstance(event, dict) or event.get("type") != "agent-turn-complete":
        return 0
    send_notification(
        platform,
        notification_executable_path,
        desktop_focus_path,
        herdr_path,
        event,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
