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


def standalone_cat_paths(tool_input, working_directory):
    command = tool_input.get("command")
    if not isinstance(command, str) or len(command) > MAXIMUM_COMMAND_CHARACTERS:
        return set()
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return set()
    if not tokens or Path(tokens[0]).name != "cat":
        return set()
    arguments = tokens[1:]
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    if not arguments or len(arguments) > MAXIMUM_READ_PATHS:
        return set()
    if any(
        argument.startswith("-")
        or any(character in argument for character in "|&;()<>`$")
        for argument in arguments
    ):
        return set()
    return {
        (Path(working_directory) / Path(argument).expanduser()).resolve()
        for argument in arguments
    }


def managed_skill_was_read(package, skill_path, read_paths):
    if skill_path.resolve() in read_paths:
        return True
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    cache = codex_home / "plugins/cache/dotagents-local/dotfiles"
    if not any(path.is_relative_to(cache.resolve()) for path in read_paths):
        return False
    try:
        with (package / "plugin.json").open("rb") as manifest_file:
            content = manifest_file.read(MAXIMUM_SKILL_BYTES + 1)
        if len(content) > MAXIMUM_SKILL_BYTES:
            return False
        manifest = json.loads(content)
    except (OSError, ValueError, UnicodeError):
        return False
    if not isinstance(manifest, dict) or manifest.get("name") != "dotfiles":
        return False
    version = manifest.get("version")
    if not isinstance(version, str) or version in {"", ".", ".."}:
        return False
    if Path(version).name != version:
        return False
    cached_skill = cache / version / skill_path.relative_to(package)
    return cached_skill.resolve() in read_paths


def handle(hook_input):
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
    working_directory = tool_input.get("cwd") or hook_input.get("cwd")
    if (
        not isinstance(working_directory, str)
        or not Path(working_directory).is_absolute()
    ):
        return None
    read_paths = standalone_cat_paths(tool_input, working_directory)
    if not read_paths:
        return None
    package = Path.home() / MANAGED_PLUGIN_DIRECTORY
    for skill_name in AUTHORING_SKILL_NAMES:
        skill_path = package / "skills" / skill_name / "SKILL.md"
        if not managed_skill_was_read(package, skill_path, read_paths):
            continue
        try:
            with skill_path.open("rb") as skill_file:
                content = skill_file.read(MAXIMUM_SKILL_BYTES + 1)
            if len(content) > MAXIMUM_SKILL_BYTES:
                continue
            skill_text = content.decode("utf-8").strip()
        except (OSError, UnicodeError):
            continue
        if skill_text and skill_text in response:
            skill_loaded_marker.record_skill_loaded(skill_name, session_id)
    return None
