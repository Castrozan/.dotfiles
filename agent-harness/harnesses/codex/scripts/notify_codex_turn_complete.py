import json
import subprocess
import sys
from pathlib import Path


NOTIFICATION_TITLE_CHARACTER_LIMIT = 100
NOTIFICATION_BODY_CHARACTER_LIMIT = 320
NOTIFICATION_TITLE_PREFIX = "Codex · "


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


def notification_arguments(
    notify_send_path: str, event: dict[str, object]
) -> list[str]:
    title_text_limit = NOTIFICATION_TITLE_CHARACTER_LIMIT - len(
        NOTIFICATION_TITLE_PREFIX
    )
    title = NOTIFICATION_TITLE_PREFIX + bound_text(
        request_text(event), title_text_limit
    )
    body = normalize_text(event.get("last-assistant-message")) or "Turn complete"
    return [
        notify_send_path,
        "--app-name",
        "Codex",
        title,
        bound_text(body, NOTIFICATION_BODY_CHARACTER_LIMIT),
    ]


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        return 0
    notify_send_path, serialized_event = arguments
    try:
        event = json.loads(serialized_event)
    except json.JSONDecodeError:
        return 0
    if not isinstance(event, dict) or event.get("type") != "agent-turn-complete":
        return 0
    try:
        subprocess.run(notification_arguments(notify_send_path, event), check=False)
    except OSError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
