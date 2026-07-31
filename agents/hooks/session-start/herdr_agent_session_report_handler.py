#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import random
import socket
import sys
import time
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from hook_dispatch import CLAUDE_SURFACE, requested_hook_surface  # noqa: E402

HERDR_REPORT_AGENT_SESSION_METHOD = "pane.report_agent_session"
HERDR_SOCKET_TIMEOUT_SECONDS = 0.5
HERDR_RESPONSE_READ_BYTES = 4096


def running_inside_a_herdr_pane() -> bool:
    return (
        os.environ.get("HERDR_ENV") == "1"
        and bool(os.environ.get("HERDR_PANE_ID"))
        and bool(os.environ.get("HERDR_SOCKET_PATH"))
    )


def reported_agent_name() -> str:
    return "claude" if requested_hook_surface() == CLAUDE_SURFACE else "codex"


def non_empty_string_or_none(value) -> str | None:
    return value if isinstance(value, str) and value else None


def build_report_agent_session_request(
    hook_input: dict, agent_name: str
) -> dict | None:
    agent_session_id = non_empty_string_or_none(hook_input.get("session_id"))
    if agent_session_id is None:
        return None
    report_source = f"herdr:{agent_name}"
    request_parameters = {
        "pane_id": os.environ["HERDR_PANE_ID"],
        "source": report_source,
        "agent": agent_name,
        "seq": time.time_ns(),
        "agent_session_id": agent_session_id,
    }
    agent_session_path = non_empty_string_or_none(hook_input.get("transcript_path"))
    if agent_session_path is not None:
        request_parameters["agent_session_path"] = agent_session_path
    session_start_source = non_empty_string_or_none(hook_input.get("source"))
    if session_start_source is not None:
        request_parameters["session_start_source"] = session_start_source
    return {
        "id": f"{report_source}:{time.time_ns()}:{random.randrange(1_000_000):06d}",
        "method": HERDR_REPORT_AGENT_SESSION_METHOD,
        "params": request_parameters,
    }


def send_request_over_the_herdr_socket(request: dict) -> None:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(HERDR_SOCKET_TIMEOUT_SECONDS)
    try:
        client.connect(os.environ["HERDR_SOCKET_PATH"])
        client.sendall((json.dumps(request) + "\n").encode())
        try:
            client.recv(HERDR_RESPONSE_READ_BYTES)
        except OSError:
            pass
    finally:
        client.close()


def handle(hook_input: dict):
    if hook_input.get("agent_id"):
        return None
    if not running_inside_a_herdr_pane():
        return None
    request = build_report_agent_session_request(hook_input, reported_agent_name())
    if request is None:
        return None
    try:
        send_request_over_the_herdr_socket(request)
    except OSError:
        return None
    return None
