#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path


def find_active_deep_work_workspaces(project_root):
    deep_work_directory = Path(project_root) / ".deep-work"
    if not deep_work_directory.is_dir():
        return []

    workspaces = []
    for workspace_path in sorted(deep_work_directory.iterdir()):
        if not workspace_path.is_dir():
            continue
        plan_file = workspace_path / "plan.md"
        if plan_file.exists():
            workspaces.append(workspace_path)
    return workspaces


def read_file_head(file_path, max_lines=20):
    try:
        with open(file_path) as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"... ({count_remaining_lines(f)} more lines)")
                    break
                lines.append(line.rstrip())
            return "\n".join(lines)
    except (OSError, UnicodeDecodeError):
        return ""


def count_remaining_lines(file_handle):
    return sum(1 for _ in file_handle)


def read_file_tail(file_path, max_lines=10):
    try:
        with open(file_path) as f:
            all_lines = f.readlines()
        tail = all_lines[-max_lines:]
        prefix = (
            f"... ({len(all_lines) - max_lines} earlier entries)\n"
            if len(all_lines) > max_lines
            else ""
        )
        return prefix + "".join(tail).rstrip()
    except (OSError, UnicodeDecodeError):
        return ""


def build_workspace_recovery_summary(workspace_path):
    workspace_name = workspace_path.name
    sections = [f"## Active deep-work: {workspace_name}"]
    sections.append(f"Workspace: {workspace_path}")

    plan_file = workspace_path / "plan.md"
    if plan_file.exists():
        sections.append("\n### Plan (current state):")
        sections.append(read_file_head(plan_file, max_lines=30))

    progress_file = workspace_path / "progress.md"
    if progress_file.exists():
        sections.append("\n### Recent progress:")
        sections.append(read_file_tail(progress_file, max_lines=15))

    context_file = workspace_path / "context.md"
    if context_file.exists():
        sections.append("\n### Key context:")
        sections.append(read_file_head(context_file, max_lines=20))

    prompts_file = workspace_path / "prompts.md"
    if prompts_file.exists():
        sections.append(
            f"\n### User prompts: {prompts_file} (read full file for verbatim requirements)"
        )

    return "\n".join(sections)


def check_heartbeat_file(project_root):
    heartbeat_path = Path(project_root) / "HEARTBEAT.md"
    if not heartbeat_path.exists():
        return ""
    content = read_file_head(heartbeat_path, max_lines=15)
    if not content.strip():
        return ""
    return f"## Active HEARTBEAT.md:\n{content}"


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    hook_event = data.get("hook_event_name", "")
    if hook_event != "SessionStart":
        sys.exit(0)

    project_root = os.getcwd()

    recovery_sections = []

    workspaces = find_active_deep_work_workspaces(project_root)
    for workspace_path in workspaces:
        recovery_sections.append(build_workspace_recovery_summary(workspace_path))

    heartbeat_summary = check_heartbeat_file(project_root)
    if heartbeat_summary:
        recovery_sections.append(heartbeat_summary)

    if not recovery_sections:
        sys.exit(0)

    recovery_context = "\n\n".join(recovery_sections)
    recovery_context += "\n\nResume from disk artifacts. Read full workspace files before continuing. Do not ask user to re-explain."

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "DEEP-WORK RECOVERY:\n" + recovery_context,
        },
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
