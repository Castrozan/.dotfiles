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
    "patch": "Edit",
}
HERMES_FILE_PATH_TOOL_NAMES = {"write_file", "patch"}
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
    tool_input = hermes_payload.get("tool_input") or {}
    payload = {
        "hook_event_name": hook_event_name,
        "tool_name": _canonical_tool_name(hermes_tool_name, tool_input),
        "tool_input": _canonical_tool_input(hermes_tool_name, tool_input),
        "session_id": hermes_payload.get("session_id", ""),
        "cwd": hermes_payload.get("cwd", os.getcwd()),
    }
    extra = hermes_payload.get("extra")
    if isinstance(extra, dict):
        if "tool_call_id" in extra:
            payload["tool_use_id"] = extra["tool_call_id"]
        if hook_event_name == "PostToolUse" and "result" in extra:
            payload["tool_response"] = extra["result"]
    return payload


def _canonical_tool_name(hermes_tool_name, tool_input):
    if (
        hermes_tool_name == "patch"
        and isinstance(tool_input, dict)
        and tool_input.get("mode") == "patch"
    ):
        return "apply_patch"
    return HERMES_TOOL_TO_CANONICAL_TOOL_NAME.get(hermes_tool_name, hermes_tool_name)


def _canonical_tool_input(hermes_tool_name, tool_input):
    if hermes_tool_name not in HERMES_FILE_PATH_TOOL_NAMES or not isinstance(
        tool_input, dict
    ):
        return tool_input
    canonical_input = tool_input.copy()
    if hermes_tool_name == "patch" and canonical_input.get("mode") == "patch":
        canonical_input.pop("path", None)
        if "patch" in canonical_input:
            canonical_input["patch_text"] = canonical_input.pop("patch")
    elif "path" in canonical_input:
        canonical_input["file_path"] = canonical_input.pop("path")
    return canonical_input


def _hermes_tool_input(hermes_tool_name, tool_input):
    if hermes_tool_name not in HERMES_FILE_PATH_TOOL_NAMES:
        return tool_input
    hermes_input = tool_input.copy()
    if "file_path" in hermes_input:
        hermes_input["path"] = hermes_input.pop("file_path")
    if hermes_tool_name == "patch" and "patch_text" in hermes_input:
        hermes_input["patch"] = hermes_input.pop("patch_text")
    return hermes_input


def hermes_response(dispatcher_output, hermes_tool_name):
    try:
        parsed_output = json.loads(dispatcher_output)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed_output, dict):
        return None
    hook_specific_response = _hermes_hook_specific_response(
        parsed_output, hermes_tool_name
    )
    if (
        hook_specific_response is not None
        and hook_specific_response.get("decision") == "block"
    ):
        return hook_specific_response
    return _hermes_top_level_response(parsed_output) or hook_specific_response


def _hermes_hook_specific_response(parsed_output, hermes_tool_name):
    hook_specific_output = parsed_output.get("hookSpecificOutput")
    if not isinstance(hook_specific_output, dict):
        return None
    permission_decision = hook_specific_output.get("permissionDecision")
    if permission_decision in BLOCKING_DECISIONS:
        return {
            "decision": "block",
            "reason": hook_specific_output.get("permissionDecisionReason")
            or parsed_output.get("reason")
            or "Blocked by the shared agent hook guard.",
        }
    updated_input = hook_specific_output.get("updatedInput")
    if permission_decision == "allow" and isinstance(updated_input, dict):
        return {
            "action": "modify",
            "args": _hermes_tool_input(hermes_tool_name, updated_input),
        }
    return None


def _hermes_top_level_response(parsed_output):
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
    response = dispatch_hermes_payload(dispatcher_launcher, hermes_payload)
    if response is not None:
        print(json.dumps(response))


def dispatch_hermes_payload(dispatcher_launcher, hermes_payload):
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
    response = hermes_response(
        completed_dispatch.stdout, hermes_payload.get("tool_name", "")
    )
    return response


if __name__ == "__main__":
    main()
