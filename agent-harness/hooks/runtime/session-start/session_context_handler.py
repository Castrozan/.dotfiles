#!/usr/bin/env python3

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from hook_dispatch import HandlerResult  # noqa: E402
from session_context_banner_formatter import (  # noqa: E402
    format_environment_section,
    format_git_section,
    format_project_context_section,
    format_system_info_section,
    format_time_sections,
)
from session_context_concurrent_gathering import gather_concurrently  # noqa: E402
from session_context_environment import check_environment  # noqa: E402
from session_context_git_status import get_git_status  # noqa: E402
from session_context_hyprland import (  # noqa: E402
    detect_hyprland_workspace_context,
    format_hyprland_workspace_section,
)
from session_context_project_context import check_project_context  # noqa: E402
from session_context_system_info import get_system_info  # noqa: E402


def handle(hook_input: dict):
    gathered = gather_concurrently(
        {
            "git": get_git_status,
            "environment": check_environment,
            "hyprland": detect_hyprland_workspace_context,
            "project": check_project_context,
            "system": get_system_info,
        }
    )

    sections = []
    for formatter, gathered_key in (
        (format_git_section, "git"),
        (format_environment_section, "environment"),
        (format_hyprland_workspace_section, "hyprland"),
        (format_project_context_section, "project"),
        (format_system_info_section, "system"),
    ):
        section = formatter(gathered[gathered_key])
        if section:
            sections.append(section)

    sections.extend(format_time_sections(datetime.now()))

    if not sections:
        return None
    return HandlerResult(additional_context="SESSION CONTEXT:\n" + "\n".join(sections))
