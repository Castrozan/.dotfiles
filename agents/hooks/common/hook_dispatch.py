#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys

from codex_tool_payload import matchable_tool_names, normalize_codex_tool_payload

DECISION_STRENGTH = {"allow": 1, "ask": 2, "block": 3, "deny": 3}

CLAUDE_SURFACE = "claude"
CODEX_SURFACE = "codex"
OPENCODE_SURFACE = "opencode"
EVERY_SURFACE = (CLAUDE_SURFACE, CODEX_SURFACE, OPENCODE_SURFACE)
SURFACE_ARGUMENT_PREFIX = "--surface="


class HandlerResult:
    def __init__(
        self,
        additional_context="",
        decision=None,
        reason="",
        system_message="",
        updated_input=None,
    ):
        self.additional_context = additional_context
        self.decision = decision
        self.reason = reason
        self.system_message = system_message
        self.updated_input = updated_input


class HookHandler:
    def __init__(self, handle, tool_matcher=None, surfaces=EVERY_SURFACE):
        self.handle = handle
        self.tool_matcher = tool_matcher
        self.surfaces = surfaces


class MergedHookOutcome:
    def __init__(self):
        self.additional_context_fragments = []
        self.decision = None
        self.reason = ""
        self.system_message_fragments = []
        self.updated_input = None

    @property
    def combined_additional_context(self) -> str:
        return "\n\n".join(
            fragment for fragment in self.additional_context_fragments if fragment
        )

    @property
    def combined_system_message(self) -> str:
        return "\n\n".join(
            fragment for fragment in self.system_message_fragments if fragment
        )


def read_hook_input_or_exit() -> dict:
    try:
        parsed_payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(parsed_payload, dict):
        sys.exit(0)
    raw_apply_patch_input = parsed_payload.get(
        "tool_name"
    ) == "apply_patch" and isinstance(parsed_payload.get("tool_input"), str)
    if (
        not isinstance(parsed_payload.get("tool_input"), dict)
        and not raw_apply_patch_input
    ):
        parsed_payload["tool_input"] = {}
    return normalize_codex_tool_payload(parsed_payload)


def dispatched_hook_input_or_exit(handled_event_names) -> dict:
    hook_input = read_hook_input_or_exit()
    reported_event_name = hook_input.get("hook_event_name", "")
    if reported_event_name and reported_event_name not in handled_event_names:
        sys.exit(0)
    return hook_input


def requested_hook_surface() -> str:
    for command_line_argument in sys.argv[1:]:
        if command_line_argument.startswith(SURFACE_ARGUMENT_PREFIX):
            return command_line_argument[len(SURFACE_ARGUMENT_PREFIX) :]
    return CLAUDE_SURFACE


def handler_runs_on_surface(handler, surface: str) -> bool:
    return surface in handler.surfaces


def handler_matches_tool(handler, tool_name: str) -> bool:
    if handler.tool_matcher is None:
        return True
    return any(
        re.fullmatch(handler.tool_matcher, candidate_tool_name) is not None
        for candidate_tool_name in matchable_tool_names(tool_name)
    )


def candidate_decision_is_stronger(candidate, current) -> bool:
    if candidate is None:
        return False
    if current is None:
        return True
    return DECISION_STRENGTH.get(candidate, 0) > DECISION_STRENGTH.get(current, 0)


def describe_handler(handler) -> str:
    handle_function = handler.handle
    return (
        getattr(handle_function, "__module__", "")
        or getattr(handle_function, "__qualname__", "")
        or "handler"
    )


def run_handlers(hook_input: dict, handlers, surface=CLAUDE_SURFACE):
    outcome = MergedHookOutcome()
    tool_name = hook_input.get("tool_name", "") or ""
    for handler in handlers:
        if not handler_runs_on_surface(handler, surface):
            continue
        if not handler_matches_tool(handler, tool_name):
            continue
        try:
            result = handler.handle(hook_input)
        except Exception as handler_error:
            outcome.system_message_fragments.append(
                f"Hook handler {describe_handler(handler)} failed and was skipped: "
                f"{type(handler_error).__name__}: {handler_error}"
            )
            continue
        if result is None:
            continue
        if result.additional_context:
            outcome.additional_context_fragments.append(result.additional_context)
        if result.system_message:
            outcome.system_message_fragments.append(result.system_message)
        if candidate_decision_is_stronger(result.decision, outcome.decision):
            outcome.decision = result.decision
            outcome.reason = result.reason
        if result.updated_input is not None and outcome.updated_input is None:
            outcome.updated_input = result.updated_input
    return outcome
