from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

import instructions_skill_marker  # noqa: E402
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
    "subagent-brief conventions; also invoke Skill(skill='review') and read its docs.md "
    "for the documentation and policy-writing principle, and read any repo-local "
    "instruction-authoring guidance in the nearest CLAUDE.md or AGENTS.md. Once you have "
    "invoked Skill(skill='instructions') this session, re-attempt this edit applying "
    "those standards and it will proceed."
)


def has_loaded_instructions_skill_this_session(session_id):
    return instructions_skill_marker.instructions_skill_loaded_marker_path(
        session_id
    ).exists()


def extract_edited_file_path(tool_input):
    return tool_input.get("file_path", "") or tool_input.get("notebook_path", "")


def is_agent_directed_instruction_file(file_path):
    if not file_path:
        return False
    path = Path(file_path)
    if path.name.lower() in INSTRUCTION_FILENAMES_THAT_ARE_ALWAYS_AGENT_DIRECTED:
        return True
    posix_path = path.as_posix()
    if any(
        posix_path == relative_path or posix_path.endswith("/" + relative_path)
        for relative_path in AGENT_DIRECTED_INSTRUCTION_RELATIVE_PATHS
    ):
        return True
    if path.suffix.lower() != ".md":
        return False
    return any(part.lower() == "skills" for part in path.parts)


def handle(hook_input):
    tool_input = hook_input.get("tool_input", {})
    file_path = extract_edited_file_path(tool_input)

    if not is_agent_directed_instruction_file(file_path):
        return None

    if has_loaded_instructions_skill_this_session(hook_input.get("session_id", "")):
        return None

    return HandlerResult(decision="deny", reason=AUTHORING_STANDARDS_DIRECTIVE)
