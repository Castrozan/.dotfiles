import re


TOOL_NAMES = {
    "shell": "Bash",
    "edit": "Edit",
    "skill": "Skill",
    "subagent": "Agent",
    "patch": "apply_patch",
    "webfetch": "WebFetch",
    "write": "Write",
}
NATIVE_ARGUMENT_NAMES = {
    "file_path": "path",
    "new_string": "newString",
    "old_string": "oldString",
    "patch_text": "patchText",
    "subagent_type": "agent",
    "skill": "id",
}


def canonical_key(key):
    if key == "path":
        return "file_path"
    return re.sub(r"[A-Z]", lambda match: "_" + match[0].lower(), key)


def map_keys(value, key_mapper):
    if isinstance(value, list):
        return [map_keys(child, key_mapper) for child in value]
    if not isinstance(value, dict):
        return value
    return {
        key_mapper(key): map_keys(child, key_mapper) for key, child in value.items()
    }


def dispatcher_payload(payload):
    result = dict(payload)
    tool_name = TOOL_NAMES.get(payload.get("tool_name"), payload.get("tool_name"))
    if tool_name is None:
        return result
    arguments = map_keys(payload.get("tool_input", {}), canonical_key)
    arguments = _normalize_tool_arguments(tool_name, arguments)
    return result | {"tool_name": tool_name, "tool_input": arguments}


def _normalize_tool_arguments(tool_name, arguments):
    if isinstance(arguments, dict):
        if _has_string_patch_payload(tool_name, arguments):
            return arguments["patch_text"]
        elif tool_name == "Agent" and "agent" in arguments:
            arguments["subagent_type"] = arguments.pop("agent")
        elif tool_name == "Skill" and "id" in arguments:
            arguments["skill"] = arguments.pop("id")
    return arguments


def _has_string_patch_payload(tool_name, arguments):
    return tool_name == "apply_patch" and isinstance(arguments.get("patch_text"), str)


def native_output(output):
    specific = output.get("hookSpecificOutput")
    if isinstance(specific, dict) and isinstance(specific.get("updatedInput"), dict):
        specific["updatedInput"] = map_keys(
            specific["updatedInput"], lambda key: NATIVE_ARGUMENT_NAMES.get(key, key)
        )
    return output
