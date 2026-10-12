from __future__ import annotations

import os
from pathlib import Path
import re
import shlex

from codex_app_server_client import CodexAppServerClient, CodexThreadTitle
from codex_session_title_state import generated_session_title_is_current
from herdr_pane_client import belongs_to_a_subagent
from hook_dispatch import HandlerResult
from servant_identity_handler import servant_for_hook_input, session_id_of
from catalog import SERVANT_CATALOG

SERVANT_NAME_PATTERN = "|".join(
    map(
        re.escape,
        sorted((servant["name"] for servant in SERVANT_CATALOG), key=len, reverse=True),
    )
)
SERVANT_PREFIX_PATTERN = re.compile(
    r"^(?:"
    + rf"\[(?:{SERVANT_NAME_PATTERN})\](?: \| | |$)"
    + "|"
    + rf"(?:{SERVANT_NAME_PATTERN})(?: \| |$)"
    + ")+"
)


def servant_thread_name(thread_title: CodexThreadTitle, servant_name: str) -> str:
    title = SERVANT_PREFIX_PATTERN.sub("", thread_title.name or "", count=1)
    title = title or thread_title.preview
    return f"{servant_name} | {title}" if title else servant_name


def thread_title_with_prompt_preview(
    thread_title: CodexThreadTitle, hook_input: dict
) -> CodexThreadTitle:
    if thread_title.preview or hook_input.get("hook_event_name") != "UserPromptSubmit":
        return thread_title
    prompt = hook_input.get("prompt", "")
    if not isinstance(prompt, str):
        return thread_title
    return CodexThreadTitle(thread_title.name, " ".join(prompt.split()))


def session_title_needs_generation(
    thread_title: CodexThreadTitle, servant_name: str
) -> bool:
    name = servant_thread_name(CodexThreadTitle(thread_title.name, ""), servant_name)
    preview = " ".join(thread_title.preview.split())
    return name == servant_name or (
        bool(preview) and " ".join(name.split()) == f"{servant_name} | {preview}"
    )


def session_title_command(
    thread_identifier: str, thread_title: CodexThreadTitle
) -> str:
    scripts_directory = Path(__file__).resolve().parent
    return shlex.join(
        [
            str(scripts_directory / "run-hook.sh"),
            str(scripts_directory / "codex_session_title.py"),
            "--thread-id",
            thread_identifier,
            "--expected-name-digest",
            thread_title.name_digest,
        ]
    )


def generated_session_title_context(
    hook_input: dict,
    thread_identifier: str,
    title: CodexThreadTitle,
    servant_name: str,
):
    if hook_input.get("hook_event_name") != "UserPromptSubmit" or not title.preview:
        return None
    if not session_title_needs_generation(title, servant_name):
        return None
    if generated_session_title_is_current(thread_identifier, title.name_digest):
        return None
    return HandlerResult(
        additional_context="Codex session title command: "
        + session_title_command(thread_identifier, title)
    )


def handle(hook_input: dict):
    socket_path = os.environ.get("CODEX_SESSION_SOCKET_PATH")
    if not socket_path or belongs_to_a_subagent(hook_input):
        return None
    servant = servant_for_hook_input(hook_input)
    if servant is None:
        return None
    thread_identifier = session_id_of(hook_input)
    with CodexAppServerClient(socket_path) as client:
        title = thread_title_with_prompt_preview(
            client.thread_title(thread_identifier), hook_input
        )
        name = servant_thread_name(CodexThreadTitle(title.name, ""), servant["name"])
        if name != title.name:
            client.set_thread_name(thread_identifier, name)
        title = CodexThreadTitle(name, title.preview)
    return generated_session_title_context(
        hook_input, thread_identifier, title, servant["name"]
    )
