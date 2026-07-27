from __future__ import annotations

import json


def emit_context_injection(event_name: str, outcome) -> None:
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


def emit_stop_decision(outcome) -> None:
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


def emit_post_tool_use_outcome(outcome) -> None:
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


def emit_pretooluse_decision(outcome) -> None:
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
