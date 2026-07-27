from __future__ import annotations

import os
import shlex

_CODEX_SHELL_TOOL_NAME = "shell"
_APPLY_PATCH_COMMAND_NAMES = ("apply_patch", "applypatch")
_SHELL_INTERPRETER_NAMES = ("bash", "sh", "zsh", "dash", "ksh")


def script_argument_of_shell_interpreter_invocation(command_argument_vector):
    if len(command_argument_vector) < 3:
        return None
    interpreter_name = os.path.basename(str(command_argument_vector[0]))
    if interpreter_name not in _SHELL_INTERPRETER_NAMES:
        return None
    for flag_index in range(1, len(command_argument_vector) - 1):
        flag = str(command_argument_vector[flag_index])
        if flag.startswith("-") and "c" in flag.lstrip("-"):
            return str(command_argument_vector[flag_index + 1])
    return None


def normalize_codex_tool_payload(hook_input: dict) -> dict:
    if not isinstance(hook_input, dict):
        return hook_input
    if hook_input.get("tool_name") != _CODEX_SHELL_TOOL_NAME:
        return hook_input

    tool_input = hook_input.get("tool_input")
    if not isinstance(tool_input, dict):
        return hook_input

    command_argument_vector = tool_input.get("command")
    if not isinstance(command_argument_vector, list) or not command_argument_vector:
        return hook_input
    if str(command_argument_vector[0]) in _APPLY_PATCH_COMMAND_NAMES:
        return hook_input

    normalized_hook_input = dict(hook_input)
    normalized_tool_input = dict(tool_input)
    interpreted_script = script_argument_of_shell_interpreter_invocation(
        command_argument_vector
    )
    normalized_tool_input["command"] = (
        interpreted_script
        if interpreted_script is not None
        else shlex.join(str(command_part) for command_part in command_argument_vector)
    )
    normalized_hook_input["tool_name"] = "Bash"
    normalized_hook_input["tool_input"] = normalized_tool_input
    return normalized_hook_input
