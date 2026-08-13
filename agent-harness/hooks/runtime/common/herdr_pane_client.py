#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import random
import socket
import time

HERDR_SOCKET_TIMEOUT_SECONDS = 0.5
HERDR_RESPONSE_READ_BYTES = 65536
SUBAGENT_HOOK_EVENT_NAME = "SubagentStop"


def running_inside_a_herdr_pane() -> bool:
    return (
        os.environ.get("HERDR_ENV") == "1"
        and bool(os.environ.get("HERDR_PANE_ID"))
        and bool(os.environ.get("HERDR_SOCKET_PATH"))
    )


def owned_by_the_clawde_supervisor() -> bool:
    return bool(os.environ.get("CLAWDE_AGENT_NAME"))


def belongs_to_a_subagent(hook_input: dict) -> bool:
    return (
        bool(hook_input.get("agent_id"))
        or hook_input.get("hook_event_name") == SUBAGENT_HOOK_EVENT_NAME
    )


def surrounding_pane_id() -> str:
    return os.environ.get("HERDR_PANE_ID", "")


def surrounding_tab_id() -> str:
    return os.environ.get("HERDR_TAB_ID", "")


def report_source_for(agent_name: str) -> str:
    return f"herdr:{agent_name}"


def request_identifier(method: str) -> str:
    return f"herdr-hook:{method}:{time.time_ns()}:{random.randrange(1_000_000):06d}"


def read_one_response_line(client: socket.socket) -> bytes:
    received_bytes = b""
    while b"\n" not in received_bytes:
        next_chunk = client.recv(HERDR_RESPONSE_READ_BYTES)
        if not next_chunk:
            break
        received_bytes += next_chunk
    return received_bytes


def ask_herdr(method: str, request_parameters: dict) -> dict | None:
    request = {
        "id": request_identifier(method),
        "method": method,
        "params": request_parameters,
    }
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(HERDR_SOCKET_TIMEOUT_SECONDS)
    try:
        client.connect(os.environ["HERDR_SOCKET_PATH"])
        client.sendall((json.dumps(request) + "\n").encode())
        response = json.loads(read_one_response_line(client).decode().splitlines()[0])
    except (IndexError, KeyError, OSError, ValueError):
        return None
    finally:
        client.close()
    returned_result = response.get("result") if isinstance(response, dict) else None
    return returned_result if isinstance(returned_result, dict) else None
