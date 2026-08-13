#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import time

shared_common_hook_modules_directory = os.path.dirname(os.path.realpath(__file__))
if shared_common_hook_modules_directory not in sys.path:
    sys.path.insert(0, shared_common_hook_modules_directory)

from herdr_pane_client import (  # noqa: E402
    ask_herdr,
    belongs_to_a_subagent,
    owned_by_the_clawde_supervisor,
    report_source_for,
    running_inside_a_herdr_pane,
    surrounding_pane_id,
)
from hook_dispatch import requested_hook_surface  # noqa: E402

HERDR_REPORT_AGENT_SESSION_METHOD = "pane.report_agent_session"


def non_empty_string_or_none(value) -> str | None:
    return value if isinstance(value, str) and value else None


def build_report_agent_session_parameters(
    hook_input: dict, agent_name: str
) -> dict | None:
    agent_session_id = non_empty_string_or_none(hook_input.get("session_id"))
    if agent_session_id is None:
        return None
    request_parameters = {
        "pane_id": surrounding_pane_id(),
        "source": report_source_for(agent_name),
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
    return request_parameters


def handle(hook_input: dict):
    if belongs_to_a_subagent(hook_input):
        return None
    if owned_by_the_clawde_supervisor():
        return None
    if not running_inside_a_herdr_pane():
        return None
    request_parameters = build_report_agent_session_parameters(
        hook_input, requested_hook_surface()
    )
    if request_parameters is None:
        return None
    ask_herdr(HERDR_REPORT_AGENT_SESSION_METHOD, request_parameters)
    return None
