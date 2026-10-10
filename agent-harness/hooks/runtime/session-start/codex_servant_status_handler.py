from __future__ import annotations

import os

from codex_app_server_client import CodexAppServerClient, CodexThreadTitle
from herdr_pane_client import belongs_to_a_subagent
from servant_identity_handler import servant_for_hook_input, session_id_of
from catalog import SERVANT_CATALOG


def servant_thread_name(thread_title: CodexThreadTitle, servant_name: str) -> str:
    title = thread_title.name or ""
    for servant in SERVANT_CATALOG:
        name = servant["name"]
        if title in (name, f"[{name}]"):
            title = ""
            break
        prefix = next(
            (
                prefix
                for prefix in (f"[{name}] | ", f"[{name}] ", f"{name} | ")
                if title.startswith(prefix)
            ),
            None,
        )
        if prefix is not None:
            title = title[len(prefix) :]
            break
    title = title or thread_title.preview
    return f"{servant_name} | {title}" if title else servant_name


def handle(hook_input: dict):
    socket_path = os.environ.get("CODEX_SESSION_SOCKET_PATH")
    if not socket_path or belongs_to_a_subagent(hook_input):
        return None
    servant = servant_for_hook_input(hook_input)
    if servant is None:
        return None
    thread_identifier = session_id_of(hook_input)
    with CodexAppServerClient(socket_path) as client:
        title = client.thread_title(thread_identifier)
        if (
            hook_input.get("hook_event_name") == "UserPromptSubmit"
            and not title.preview
        ):
            prompt = hook_input.get("prompt", "")
            if isinstance(prompt, str):
                title = CodexThreadTitle(title.name, " ".join(prompt.split()))
        name = servant_thread_name(title, servant["name"])
        if name != title.name:
            client.set_thread_name(thread_identifier, name)
    return None
