import json
import os
import subprocess
import sys

HERMES_EVENT_TO_HOOK_EVENT_NAME = {
    "pre_tool_call": "PreToolUse",
    "post_tool_call": "PostToolUse",
}
HERMES_TOOL_TO_CANONICAL_TOOL_NAME = {
    "terminal": "Bash",
    "shell": "Bash",
    "write_file": "Write",
    "edit_file": "Edit",
}
DISPATCHER_BY_HOOK_EVENT_NAME = {
    "PreToolUse": "pre-tool-use-dispatcher.py",
    "PostToolUse": "post-tool-use-dispatcher.py",
}
BLOCKING_DECISIONS = {"block", "deny"}


def dispatcher_payload(hermes_payload):
    hook_event_name = HERMES_EVENT_TO_HOOK_EVENT_NAME.get(
        hermes_payload.get("hook_event_name")
    )
    if hook_event_name is None:
        return None
    hermes_tool_name = hermes_payload.get("tool_name", "")
    return {
        "hook_event_name": hook_event_name,
        "tool_name": HERMES_TOOL_TO_CANONICAL_TOOL_NAME.get(
            hermes_tool_name, hermes_tool_name
        ),
        "tool_input": hermes_payload.get("tool_input") or {},
        "session_id": hermes_payload.get("session_id", ""),
        "cwd": hermes_payload.get("cwd", os.getcwd()),
    }


def hermes_response(dispatcher_output):
    try:
        parsed_output = json.loads(dispatcher_output)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed_output, dict):
        return None
    hook_specific_output = parsed_output.get("hookSpecificOutput")
    if isinstance(hook_specific_output, dict):
        permission_decision = hook_specific_output.get("permissionDecision")
        if permission_decision in BLOCKING_DECISIONS:
            return {
                "decision": "block",
                "reason": hook_specific_output.get("permissionDecisionReason")
                or parsed_output.get("reason")
                or "Blocked by the shared agent hook guard.",
            }
    if parsed_output.get("decision") in BLOCKING_DECISIONS:
        return {
            "decision": "block",
            "reason": parsed_output.get("reason")
            or parsed_output.get("systemMessage")
            or "Blocked by the shared agent hook guard.",
        }
    return None


def main():
    dispatcher_launcher = sys.argv[1]
    try:
        hermes_payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    if not isinstance(hermes_payload, dict):
        return
    payload = dispatcher_payload(hermes_payload)
    if payload is None:
        return
    completed_dispatch = subprocess.run(
        [
            dispatcher_launcher,
            DISPATCHER_BY_HOOK_EVENT_NAME[payload["hook_event_name"]],
        ],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    response = hermes_response(completed_dispatch.stdout)
    if response is not None:
        print(json.dumps(response))


if __name__ == "__main__":
    main()
