#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import random
import socket
import sys
import time

shared_common_hook_modules_directory = os.path.dirname(os.path.realpath(__file__))
if shared_common_hook_modules_directory not in sys.path:
    sys.path.insert(0, shared_common_hook_modules_directory)

from hook_dispatch import CLAUDE_SURFACE, requested_hook_surface  # noqa: E402

HERDR_SOCKET_TIMEOUT_SECONDS = 0.5
HERDR_RESPONSE_READ_BYTES = 4096
SUBAGENT_HOOK_EVENT_NAME = "SubagentStop"


def running_inside_a_herdr_pane() -> bool:
    return (
        os.environ.get("HERDR_ENV") == "1"
        and bool(os.environ.get("HERDR_PANE_ID"))
        and bool(os.environ.get("HERDR_SOCKET_PATH"))
    )


def reported_agent_name() -> str:
    return "claude" if requested_hook_surface() == CLAUDE_SURFACE else "codex"


def report_source_for_agent(agent_name: str) -> str:
    return f"herdr:{agent_name}"


def non_empty_string_or_none(value) -> str | None:
    return value if isinstance(value, str) and value else None


def belongs_to_a_subagent(hook_input: dict) -> bool:
    return (
        bool(hook_input.get("agent_id"))
        or hook_input.get("hook_event_name") == SUBAGENT_HOOK_EVENT_NAME
    )


def build_request(method: str, report_source: str, request_parameters: dict) -> dict:
    return {
        "id": f"{report_source}:{time.time_ns()}:{random.randrange(1_000_000):06d}",
        "method": method,
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
