#!/usr/bin/env python3

import json
import sys
from pathlib import Path

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


def load_instructions_skill_marker_module():
    hook_script_directory = Path(__file__).resolve().parent
    shared_common_hook_modules_directory = (
        hook_script_directory.parent.parent / "common"
    )
    for candidate_directory in (
        hook_script_directory,
        shared_common_hook_modules_directory,
    ):
        candidate_directory_string = str(candidate_directory)
        if candidate_directory.is_dir() and candidate_directory_string not in sys.path:
            sys.path.insert(0, candidate_directory_string)
    import instructions_skill_marker

    return instructions_skill_marker


def has_loaded_instructions_skill_this_session(session_id):
    instructions_skill_marker = load_instructions_skill_marker_module()
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


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = extract_edited_file_path(tool_input)

    if not is_agent_directed_instruction_file(file_path):
        sys.exit(0)

    if has_loaded_instructions_skill_this_session(hook_input.get("session_id", "")):
        sys.exit(0)

    print(AUTHORING_STANDARDS_DIRECTIVE, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
