"""Render gathered context dictionaries into the human-readable banner sections."""

from datetime import datetime
from typing import Any, Dict


def format_git_section(git: Dict[str, Any]) -> str | None:
    if not git.get("is_repo"):
        return None
    git_lines = []
    if git.get("branch"):
        git_lines.append(f"Branch: {git['branch']}")
    if git.get("ahead", 0) > 0:
        git_lines.append(f"Ahead by {git['ahead']} commit(s)")
    if git.get("behind", 0) > 0:
        git_lines.append(f"Behind by {git['behind']} commit(s)")
    if git.get("uncommitted", 0) > 0:
        git_lines.append(f"Uncommitted: {git['uncommitted']} file(s)")
    if git.get("last_commit"):
        git_lines.append(f"Last: {git['last_commit']}")
    if not git_lines:
        return None
    return "Git: " + " | ".join(git_lines)


def format_environment_section(env: dict) -> str | None:
    if not env:
        return None
    env_items = [f"{k}: {v}" for k, v in env.items()]
    return "Env: " + " | ".join(env_items)


def format_project_context_section(context: list[str]) -> str | None:
    if not context:
        return None
    return "Context: " + ", ".join(context)


def format_system_info_section(sys_info: Dict[str, str]) -> str | None:
    sys_parts = []
    if sys_info.get("user"):
        sys_parts.append(f"User: {sys_info['user']}")
    if sys_info.get("os"):
        sys_parts.append(f"OS: {sys_info['os']}")
    if not sys_parts:
        return None
    return " | ".join(sys_parts)


def format_time_sections(now: datetime) -> list[str]:
    sections = [f"Date: {now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%A')})"]
    if now.hour >= 18:
        sections.append("Note: After hours - avoid risky deployments")
    return sections
