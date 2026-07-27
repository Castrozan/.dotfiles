#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

DECISION_STRENGTH = {"allow": 1, "ask": 2, "block": 3, "deny": 3}


@dataclass
class HandlerResult:
    additional_context: str = ""
    decision: Optional[str] = None
    reason: str = ""
    system_message: str = ""
    updated_input: Optional[dict] = None


@dataclass
class HookHandler:
    handle: Callable[[dict], "Optional[HandlerResult]"]
    tool_matcher: Optional[str] = None


@dataclass
class MergedHookOutcome:
    additional_context_fragments: list = field(default_factory=list)
    decision: Optional[str] = None
    reason: str = ""
    system_message_fragments: list = field(default_factory=list)
    updated_input: Optional[dict] = None

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
    if not isinstance(parsed_payload.get("tool_input"), dict):
        parsed_payload["tool_input"] = {}
    return parsed_payload


def handler_matches_tool(handler: HookHandler, tool_name: str) -> bool:
    if handler.tool_matcher is None:
        return True
    return re.fullmatch(handler.tool_matcher, tool_name or "") is not None


def candidate_decision_is_stronger(
    candidate: Optional[str], current: Optional[str]
) -> bool:
    if candidate is None:
        return False
    if current is None:
        return True
    return DECISION_STRENGTH.get(candidate, 0) > DECISION_STRENGTH.get(current, 0)


def describe_handler(handler: HookHandler) -> str:
    handle_function = handler.handle
    return (
        getattr(handle_function, "__module__", "")
        or getattr(handle_function, "__qualname__", "")
        or "handler"
    )


def run_handlers(hook_input: dict, handlers) -> MergedHookOutcome:
    outcome = MergedHookOutcome()
    tool_name = hook_input.get("tool_name", "") or ""
    for handler in handlers:
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


def emit_context_injection(event_name: str, outcome: MergedHookOutcome) -> None:
    combined_context = outcome.combined_additional_context
    if not combined_context:
        return
    print(
        json.dumps(
            {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": event_name,
                    "additionalContext": combined_context,
                },
            }
        )
    )


def emit_stop_decision(outcome: MergedHookOutcome) -> None:
    payload: dict = {}
    system_message = outcome.combined_system_message
    if system_message:
        payload["continue"] = True
        payload["systemMessage"] = system_message
    if outcome.decision == "block":
        payload["decision"] = "block"
        payload["reason"] = outcome.reason
    if payload:
        print(json.dumps(payload))


def emit_post_tool_use_outcome(outcome: MergedHookOutcome) -> None:
    payload: dict = {}
    system_message = outcome.combined_system_message
    if system_message:
        payload["systemMessage"] = system_message
    if outcome.decision == "block":
        payload["decision"] = "block"
        payload["reason"] = outcome.reason
    combined_context = outcome.combined_additional_context
    if combined_context:
        payload["hookSpecificOutput"] = {
            "hookEventName": "PostToolUse",
            "additionalContext": combined_context,
        }
    if payload:
        payload["continue"] = True
        print(json.dumps(payload))


def emit_pretooluse_decision(outcome: MergedHookOutcome) -> None:
    hook_specific_output: dict = {"hookEventName": "PreToolUse"}
    if outcome.decision is not None:
        hook_specific_output["permissionDecision"] = outcome.decision
        if outcome.reason:
            hook_specific_output["permissionDecisionReason"] = outcome.reason
    if outcome.updated_input is not None:
        hook_specific_output["updatedInput"] = outcome.updated_input
    combined_context = outcome.combined_additional_context
    if combined_context:
        hook_specific_output["additionalContext"] = combined_context
    payload: dict = {}
    system_message = outcome.combined_system_message
    if system_message:
        payload["systemMessage"] = system_message
    if len(hook_specific_output) > 1:
        payload["hookSpecificOutput"] = hook_specific_output
    if payload:
        payload["continue"] = True
        print(json.dumps(payload))
