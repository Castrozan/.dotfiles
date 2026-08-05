from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ANCESTOR_DIRECTORY = _MODULE_DIRECTORY
_SHARED_MODULE_CANDIDATE_DIRECTORIES = [_MODULE_DIRECTORY]
while _ANCESTOR_DIRECTORY != os.path.dirname(_ANCESTOR_DIRECTORY):
    _ANCESTOR_DIRECTORY = os.path.dirname(_ANCESTOR_DIRECTORY)
    _SHARED_MODULE_CANDIDATE_DIRECTORIES.append(
        os.path.join(_ANCESTOR_DIRECTORY, "common")
    )
for _shared_module_candidate_directory in _SHARED_MODULE_CANDIDATE_DIRECTORIES:
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

import skill_loaded_marker  # noqa: E402
from changed_file_paths import collect_changed_file_paths  # noqa: E402
from file_path_components import path_components  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402

INSTRUCTION_FILENAMES_THAT_ARE_ALWAYS_AGENT_DIRECTED = {"claude.md", "agents.md"}

AGENT_DIRECTED_INSTRUCTION_RELATIVE_PATHS = {
    "agents/dotfiles.md",
    "agents/core_rules/core.md",
    "agents/core_rules/core-skill-frontmatter.md",
    "agents/snippets/rebuild.md",
}

AUTHORING_STANDARDS_DIRECTIVE = (
    "BLOCKED: this file instructs an AI agent, so it must be authored against the "
    "instruction-authoring standards. This guard blocks every edit to an AI instruction "
    "file until you have loaded those standards into context this session by invoking "
    "Skill(skill='instructions') for the SKILL.md, CLAUDE.md, agent-definition, and "
    "subagent-brief conventions; also invoke Skill(skill='docs') for the documentation "
    "and policy-writing principle, and read any repo-local "
    "instruction-authoring guidance in the nearest CLAUDE.md or AGENTS.md. Once you have "
    "invoked Skill(skill='instructions') this session, re-attempt this edit applying "
    "those standards and it will proceed."
)


def has_loaded_instructions_skill_this_session(session_id):
    return skill_loaded_marker.has_skill_loaded("instructions", session_id)


def is_agent_directed_instruction_file(file_path):
    if not file_path:
        return False
    path_parts = path_components(file_path)
    file_name = os.path.basename(file_path).lower()
    if file_name in INSTRUCTION_FILENAMES_THAT_ARE_ALWAYS_AGENT_DIRECTED:
        return True
    if any(
        file_path == relative_path or file_path.endswith("/" + relative_path)
        for relative_path in AGENT_DIRECTED_INSTRUCTION_RELATIVE_PATHS
    ):
        return True
    if os.path.splitext(file_path)[1].lower() != ".md":
        return False
    return any(part.lower() == "skills" for part in path_parts)


def handle(hook_input):
    edited_paths = collect_changed_file_paths(hook_input)
    if not any(is_agent_directed_instruction_file(path) for path in edited_paths):
        return None

    if has_loaded_instructions_skill_this_session(hook_input.get("session_id", "")):
        return None

    return HandlerResult(decision="deny", reason=AUTHORING_STANDARDS_DIRECTIVE)
