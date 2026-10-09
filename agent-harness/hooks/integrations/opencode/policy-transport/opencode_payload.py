TOOL_NAMES = {
    "shell": "Bash",
    "edit": "Edit",
    "skill": "Skill",
    "subagent": "Agent",
    "patch": "apply_patch",
    "webfetch": "WebFetch",
    "write": "Write",
}
CANONICAL_ARGUMENT_NAMES = {
    "edit": {
        "path": "file_path",
        "newString": "new_string",
        "oldString": "old_string",
        "replaceAll": "replace_all",
    },
    "write": {"path": "file_path"},
    "patch": {"patchText": "patch_text"},
    "subagent": {"agent": "subagent_type"},
    "skill": {"id": "skill"},
}


def dispatcher_payload(payload):
    result = dict(payload)
    native_tool_name = payload.get("tool_name")
    if native_tool_name not in TOOL_NAMES:
        return result
    arguments = payload.get("tool_input", {})
    if isinstance(arguments, dict):
        names = CANONICAL_ARGUMENT_NAMES.get(native_tool_name, {})
        arguments = {names.get(key, key): value for key, value in arguments.items()}
        if native_tool_name == "patch" and isinstance(arguments.get("patch_text"), str):
            arguments = arguments["patch_text"]
    return result | {"tool_name": TOOL_NAMES[native_tool_name], "tool_input": arguments}


def native_output(output, native_tool_name):
    specific = output.get("hookSpecificOutput")
    if native_tool_name not in TOOL_NAMES or not isinstance(specific, dict):
        return dict(output)
    updated_input = specific.get("updatedInput")
    if native_tool_name == "patch" and isinstance(updated_input, str):
        updated_input = {"patchText": updated_input}
    elif isinstance(updated_input, dict):
        names = {
            canonical: native
            for native, canonical in CANONICAL_ARGUMENT_NAMES.get(
                native_tool_name, {}
            ).items()
        }
        updated_input = {
            names.get(key, key): value for key, value in updated_input.items()
        }
    else:
        return dict(output)
    return output | {"hookSpecificOutput": specific | {"updatedInput": updated_input}}
