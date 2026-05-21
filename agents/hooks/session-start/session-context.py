#!/usr/bin/env python3
"""session-context.py - Show relevant context at session start."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from session_context_banner_formatter import (  # noqa: E402
    format_environment_section,
    format_git_section,
    format_project_context_section,
    format_system_info_section,
    format_time_sections,
)
from session_context_environment import check_environment  # noqa: E402
from session_context_git_status import get_git_status  # noqa: E402
from session_context_hyprland import (  # noqa: E402
    detect_hyprland_workspace_context,
    format_hyprland_workspace_section,
)
from session_context_project_context import check_project_context  # noqa: E402
from session_context_system_info import get_system_info  # noqa: E402


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = data.get("hook_event_name", "")
    if hook_event != "SessionStart":
        sys.exit(0)

    sections = []

    git_section = format_git_section(get_git_status())
    if git_section:
        sections.append(git_section)

    env_section = format_environment_section(check_environment())
    if env_section:
        sections.append(env_section)

    hyprland_section = format_hyprland_workspace_section(
        detect_hyprland_workspace_context()
    )
    if hyprland_section:
        sections.append(hyprland_section)

    project_section = format_project_context_section(check_project_context())
    if project_section:
        sections.append(project_section)

    system_section = format_system_info_section(get_system_info())
    if system_section:
        sections.append(system_section)

    sections.extend(format_time_sections(datetime.now()))

    if sections:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "SESSION CONTEXT:\n" + "\n".join(sections),
            },
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
