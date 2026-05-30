#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path

STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE = (
    "AGENT_INSTRUCTION_AUTHORING_ROUTER_STATE_DIRECTORY"
)

INSTRUCTION_FILENAMES_THAT_ARE_ALWAYS_AGENT_DIRECTED = {"claude.md", "agents.md"}

AUTHORING_STANDARDS_DIRECTIVE = (
    "BLOCKED: this file instructs an AI agent, so it must be authored against the "
    "instruction-authoring standards before you edit it. First invoke "
    "Skill(skill='instructions') for the SKILL.md, CLAUDE.md, agent-definition, and "
    "subagent-brief conventions; invoke Skill(skill='review') and read its docs.md for "
    "the documentation and policy-writing principle; and read any repo-local "
    "instruction-authoring guidance in the nearest CLAUDE.md or AGENTS.md. Then "
    "re-attempt this edit applying those standards. This guard fires once per file per "
    "session, so the re-attempt proceeds."
)


def resolve_state_directory():
    override = os.environ.get(STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE)
    if override:
        return Path(override)
    return Path("/tmp")


def state_path_for_session(session_id):
    sanitized_session_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id or "unknown")
    return (
        resolve_state_directory()
        / f"agent-instruction-authoring-router-{sanitized_session_id}.json"
    )


def load_already_nudged_target_paths(state_path):
    if not state_path.exists():
        return set()
    try:
        return set(json.loads(state_path.read_text()))
    except (json.JSONDecodeError, OSError):
        return set()


def persist_already_nudged_target_paths(state_path, target_paths):
    try:
        state_path.write_text(json.dumps(sorted(target_paths)))
    except OSError:
        pass


def extract_edited_file_path(tool_input):
    return tool_input.get("file_path", "") or tool_input.get("notebook_path", "")


def is_agent_directed_instruction_file(file_path):
    if not file_path:
        return False
    path = Path(file_path)
    if path.name.lower() in INSTRUCTION_FILENAMES_THAT_ARE_ALWAYS_AGENT_DIRECTED:
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

    resolved_target_path = str(Path(file_path).expanduser())
    state_path = state_path_for_session(hook_input.get("session_id", ""))
    already_nudged_target_paths = load_already_nudged_target_paths(state_path)

    if resolved_target_path in already_nudged_target_paths:
        sys.exit(0)

    already_nudged_target_paths.add(resolved_target_path)
    persist_already_nudged_target_paths(state_path, already_nudged_target_paths)

    print(AUTHORING_STANDARDS_DIRECTIVE, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
