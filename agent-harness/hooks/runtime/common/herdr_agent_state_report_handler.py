#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import time

shared_common_hook_modules_directory = os.path.dirname(os.path.realpath(__file__))
if shared_common_hook_modules_directory not in sys.path:
    sys.path.insert(0, shared_common_hook_modules_directory)

from herdr_pane_report import (  # noqa: E402
    belongs_to_a_subagent,
    build_request,
    non_empty_string_or_none,
    report_source_for_agent,
    reported_agent_name,
    running_inside_a_herdr_pane,
    send_request_over_the_herdr_socket,
)

HERDR_REPORT_AGENT_METHOD = "pane.report_agent"

AGENT_STATE_BY_HOOK_EVENT = {
    "SessionStart": "idle",
    "UserPromptSubmit": "working",
    "Stop": "idle",
}


def agent_state_for_hook_event(hook_event_name: str | None) -> str | None:
    if hook_event_name is None:
        return None
    return AGENT_STATE_BY_HOOK_EVENT.get(hook_event_name)


def build_report_agent_request(hook_input: dict, agent_name: str) -> dict | None:
    agent_state = agent_state_for_hook_event(hook_input.get("hook_event_name"))
    if agent_state is None:
        return None
    report_source = report_source_for_agent(agent_name)
    request_parameters = {
        "pane_id": os.environ["HERDR_PANE_ID"],
        "source": report_source,
        "agent": agent_name,
        "state": agent_state,
        "seq": time.time_ns(),
    }
    agent_session_id = non_empty_string_or_none(hook_input.get("session_id"))
    if agent_session_id is not None:
        request_parameters["agent_session_id"] = agent_session_id
    return build_request(HERDR_REPORT_AGENT_METHOD, report_source, request_parameters)


def handle(hook_input: dict):
    if belongs_to_a_subagent(hook_input):
        return None
    if not running_inside_a_herdr_pane():
        return None
    request = build_report_agent_request(hook_input, reported_agent_name())
    if request is None:
        return None
    try:
        send_request_over_the_herdr_socket(request)
    except OSError:
        return None
    return None
