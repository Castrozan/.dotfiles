from pathlib import Path
import json
import os
import shlex

import skill_loaded_marker

AUTHORING_SKILL_NAMES = ("instructions", "docs")
MAXIMUM_SKILL_BYTES = 65536
MAXIMUM_COMMAND_CHARACTERS = 16384
MAXIMUM_READ_PATHS = 16
MANAGED_PLUGIN_DIRECTORY = ".local/share/agent-plugins/dotfiles/plugin"


def _cat_tokens(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return set()
    return tokens


def _cat_command_arguments(tokens):
    if not tokens or Path(tokens[0]).name != "cat":
        return None
    arguments = tokens[1:]
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    return arguments


def _cat_arguments_are_safe(arguments):
    if not arguments or len(arguments) > MAXIMUM_READ_PATHS:
        return False
    return not any(
        argument.startswith("-")
        or any(character in argument for character in "|&;()<>`$")
        for argument in arguments
    )


def standalone_cat_paths(tool_input, working_directory):
    command = tool_input.get("command")
    if not isinstance(command, str) or len(command) > MAXIMUM_COMMAND_CHARACTERS:
        return set()
    tokens = _cat_tokens(command)
    arguments = _cat_command_arguments(tokens)
    if arguments is None or not _cat_arguments_are_safe(arguments):
        return set()
    return {
        (Path(working_directory) / Path(argument).expanduser()).resolve()
        for argument in arguments
    }


def _managed_plugin_cache_directory():
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    return codex_home / "plugins/cache/dotagents-local/dotfiles"


def _read_path_is_in_managed_plugin_cache(cache, read_paths):
    return any(path.is_relative_to(cache.resolve()) for path in read_paths)


def _managed_plugin_manifest(package):
    try:
        with (package / "plugin.json").open("rb") as manifest_file:
            content = manifest_file.read(MAXIMUM_SKILL_BYTES + 1)
        if len(content) > MAXIMUM_SKILL_BYTES:
            return None
        manifest = json.loads(content)
    except (OSError, ValueError):
        return None
    if not isinstance(manifest, dict) or manifest.get("name") != "dotfiles":
        return None
    return manifest


def _managed_plugin_version(manifest):
    version = manifest.get("version")
    if not isinstance(version, str) or version in {"", ".", ".."}:
        return None
    if Path(version).name != version:
        return None
    return version


def managed_skill_was_read(package, skill_path, read_paths):
    if skill_path.resolve() in read_paths:
        return True
    cache = _managed_plugin_cache_directory()
    if not _read_path_is_in_managed_plugin_cache(cache, read_paths):
        return False
    manifest = _managed_plugin_manifest(package)
    if manifest is None:
        return False
    version = _managed_plugin_version(manifest)
    if version is None:
        return False
    cached_skill = cache / version / skill_path.relative_to(package)
    return cached_skill.resolve() in read_paths


def _skill_read_response_context(hook_input):
    session_id = hook_input.get("session_id")
    tool_input = hook_input.get("tool_input")
    response = hook_input.get("tool_response")
    if (
        not isinstance(session_id, str)
        or not session_id.strip()
        or not isinstance(tool_input, dict)
        or not isinstance(response, str)
    ):
        return None
    return session_id, tool_input, response


def _validated_skill_read_context(hook_input):
    response_context = _skill_read_response_context(hook_input)
    if response_context is None:
        return None
    session_id, tool_input, response = response_context
    working_directory = tool_input.get("cwd") or hook_input.get("cwd")
    if (
        not isinstance(working_directory, str)
        or not Path(working_directory).is_absolute()
    ):
        return None
    return session_id, tool_input, response, working_directory


def _record_authoring_skill(package, skill_name, session_id, response, read_paths):
    skill_path = package / "skills" / skill_name / "SKILL.md"
    if not managed_skill_was_read(package, skill_path, read_paths):
        return
    try:
        with skill_path.open("rb") as skill_file:
            content = skill_file.read(MAXIMUM_SKILL_BYTES + 1)
        if len(content) > MAXIMUM_SKILL_BYTES:
            return
        skill_text = content.decode("utf-8").strip()
    except (OSError, UnicodeError):
        return
    if skill_text and skill_text in response:
        skill_loaded_marker.record_skill_loaded(skill_name, session_id)


def _record_loaded_authoring_skills(package, session_id, response, read_paths):
    for skill_name in AUTHORING_SKILL_NAMES:
        _record_authoring_skill(package, skill_name, session_id, response, read_paths)


def handle(hook_input):
    context = _validated_skill_read_context(hook_input)
    if context is None:
        return None
    session_id, tool_input, response, working_directory = context
    read_paths = standalone_cat_paths(tool_input, working_directory)
    if not read_paths:
        return None
    package = Path.home() / MANAGED_PLUGIN_DIRECTORY
    _record_loaded_authoring_skills(package, session_id, response, read_paths)
    return None
