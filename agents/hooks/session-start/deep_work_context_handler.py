from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in (
    _MODULE_DIRECTORY,
    _MODULE_DIRECTORY.parent / "common",
):
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402

DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE = "DEEP_WORK_CONTEXT_DIRECTORY"
DEEP_WORK_DIRECTORY_RELATIVE_TO_HOME = ".dotfiles/.deep-work"
PROGRESS_FILENAME = "progress.md"
SECONDS_PER_HOUR = 3600
HOURS_BEFORE_A_WORKSPACE_IS_STALE = 48
WORKSPACES_NAMED_IN_THE_STALE_REPORT = 8


def deep_work_directory() -> Path:
    configured_directory = os.environ.get(DEEP_WORK_DIRECTORY_ENVIRONMENT_VARIABLE)
    if configured_directory:
        return Path(configured_directory)
    return Path.home() / DEEP_WORK_DIRECTORY_RELATIVE_TO_HOME


def hours_since_last_progress(workspace: Path) -> float:
    progress_file = workspace / PROGRESS_FILENAME
    candidates = (
        [progress_file] if progress_file.exists() else list(workspace.iterdir())
    )
    modification_times = []
    for candidate in candidates:
        try:
            modification_times.append(candidate.stat().st_mtime)
        except OSError:
            continue
    if not modification_times:
        return float("inf")
    return (time.time() - max(modification_times)) / SECONDS_PER_HOUR


def workspaces_by_staleness():
    try:
        workspaces = sorted(
            candidate
            for candidate in deep_work_directory().iterdir()
            if candidate.is_dir()
        )
    except OSError:
        return [], []
    aged = [
        (workspace, hours_since_last_progress(workspace)) for workspace in workspaces
    ]
    active = sorted(
        (entry for entry in aged if entry[1] <= HOURS_BEFORE_A_WORKSPACE_IS_STALE),
        key=lambda entry: entry[1],
    )
    stale = sorted(
        (entry for entry in aged if entry[1] > HOURS_BEFORE_A_WORKSPACE_IS_STALE),
        key=lambda entry: entry[1],
    )
    return active, stale


def describe_age(hours: float) -> str:
    if hours < 1:
        return "under an hour ago"
    if hours < 48:
        return f"{round(hours)}h ago"
    return f"{round(hours / 24)}d ago"


def format_active_section(active) -> str:
    lines = [
        f"DEEP WORK: {len(active)} active workspace(s) in .deep-work/. Read the "
        "workspace files (prompts.md, plan.md, progress.md, context.md) before "
        "continuing rather than asking what was already captured:"
    ]
    lines.extend(
        f"  {workspace.name} (last progress {describe_age(hours)})"
        for workspace, hours in active
    )
    return "\n".join(lines)


def format_stale_section(stale) -> str:
    named = ", ".join(
        workspace.name for workspace, _ in stale[:WORKSPACES_NAMED_IN_THE_STALE_REPORT]
    )
    remainder = len(stale) - WORKSPACES_NAMED_IN_THE_STALE_REPORT
    if remainder > 0:
        named = f"{named}, and {remainder} more"
    return (
        f"STALE: {len(stale)} workspace(s) with no progress in "
        f"{HOURS_BEFORE_A_WORKSPACE_IS_STALE}h: {named}. The deep-work contract says "
        "to report these rather than silently resume or delete them, so raise them "
        "with the user if they look delivered."
    )


def handle(hook_input: dict):
    active, stale = workspaces_by_staleness()
    if not active and not stale:
        return None
    sections = []
    if active:
        sections.append(format_active_section(active))
    if stale:
        sections.append(format_stale_section(stale))
    return HandlerResult(additional_context="\n\n".join(sections))
