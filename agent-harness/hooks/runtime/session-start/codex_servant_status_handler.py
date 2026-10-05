from __future__ import annotations

import os

from codex_app_server_client import CodexAppServerClient
from herdr_pane_client import belongs_to_a_subagent
from servant_identity_handler import servant_for_hook_input, session_id_of
from catalog import SERVANT_CATALOG


def servant_thread_name(thread_name: str | None, servant_name: str) -> str:
    title = thread_name or ""
    for servant in SERVANT_CATALOG:
        name = servant["name"]
        if title == name:
            title = ""
            break
        prefix = f"[{name}] "
        if title.startswith(prefix):
            title = title[len(prefix) :]
            break
    return f"[{servant_name}] {title}" if title else servant_name


def handle(hook_input: dict):
    socket_path = os.environ.get("CODEX_SESSION_SOCKET_PATH")
    if not socket_path or belongs_to_a_subagent(hook_input):
        return None
    servant = servant_for_hook_input(hook_input)
    if servant is None:
        return None
    thread_identifier = session_id_of(hook_input)
    with CodexAppServerClient(socket_path) as client:
        existing_name = client.thread_name(thread_identifier)
        name = servant_thread_name(existing_name, servant["name"])
        if name != existing_name:
            client.set_thread_name(thread_identifier, name)
    return None
