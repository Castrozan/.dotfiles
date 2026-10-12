from __future__ import annotations

import argparse
import os
import sys

from codex_app_server_client import (
    CodexAppServerClient,
    CodexAppServerError,
    CodexThreadTitle,
)
from codex_servant_status_handler import session_title_needs_generation
from codex_session_title_state import (
    generated_session_title_is_current,
    record_generated_session_title,
)
from servant_identity_handler import servant_for_hook_input


def validated_task_title(task_title: str) -> str:
    title = " ".join(task_title.split())
    if not all((title, len(title) <= 80, "|" not in title, title.isprintable())):
        raise ValueError(
            "Use a plain task title of 1–80 characters without a Servant prefix"
        )
    return title


def session_title_can_be_generated(
    thread_identifier: str,
    current_title: CodexThreadTitle,
    servant_name: str,
    expected_name_digest: str,
) -> bool:
    return all(
        (
            current_title.name_digest == expected_name_digest,
            not generated_session_title_is_current(
                thread_identifier, current_title.name_digest
            ),
            session_title_needs_generation(current_title, servant_name),
        )
    )


def set_generated_session_title(
    thread_identifier: str, expected_name_digest: str, task_title: str
) -> bool:
    title = validated_task_title(task_title)
    socket_path = os.environ.get("CODEX_SESSION_SOCKET_PATH")
    servant = servant_for_hook_input({"thread_id": thread_identifier})
    if not socket_path or servant is None:
        raise ValueError("This command requires a private interactive Codex session")
    with CodexAppServerClient(socket_path) as client:
        current_title = client.thread_title(thread_identifier)
        if not session_title_can_be_generated(
            thread_identifier, current_title, servant["name"], expected_name_digest
        ):
            return False
        name = f"{servant['name']} | {title}"
        client.set_thread_name(thread_identifier, name)
        record_generated_session_title(
            thread_identifier, CodexThreadTitle(name, current_title.preview).name_digest
        )
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--expected-name-digest", required=True)
    parser.add_argument("task_title")
    arguments = parser.parse_args()
    try:
        changed = set_generated_session_title(
            arguments.thread_id,
            arguments.expected_name_digest,
            arguments.task_title,
        )
    except (ValueError, OSError, TimeoutError, CodexAppServerError) as error:
        print(f"Could not set Codex session title: {error}", file=sys.stderr)
        return 1
    print("Session title saved" if changed else "Session title already set or changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
