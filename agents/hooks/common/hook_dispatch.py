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


@dataclass
class HookHandler:
    handle: Callable[[dict], "Optional[HandlerResult]"]
    tool_matcher: Optional[str] = None


@dataclass
class MergedHookOutcome:
    additional_context_fragments: list = field(default_factory=list)
    decision: Optional[str] = None
    reason: str = ""

    @property
    def combined_additional_context(self) -> str:
        return "\n\n".join(
            fragment for fragment in self.additional_context_fragments if fragment
        )


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


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


def run_handlers(hook_input: dict, handlers) -> MergedHookOutcome:
    outcome = MergedHookOutcome()
    tool_name = hook_input.get("tool_name", "") or ""
    for handler in handlers:
        if not handler_matches_tool(handler, tool_name):
            continue
        result = handler.handle(hook_input)
        if result is None:
            continue
        if result.additional_context:
            outcome.additional_context_fragments.append(result.additional_context)
        if candidate_decision_is_stronger(result.decision, outcome.decision):
            outcome.decision = result.decision
            outcome.reason = result.reason
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
    if outcome.decision != "block":
        return
    print(json.dumps({"decision": "block", "reason": outcome.reason}))
