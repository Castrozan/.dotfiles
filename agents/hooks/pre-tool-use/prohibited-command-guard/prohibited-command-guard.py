#!/usr/bin/env python3
from __future__ import annotations

import json
import re
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

from codex_tool_payload import normalize_codex_tool_payload  # noqa: E402
from pre_tool_use_block import deny_pre_tool_use_call  # noqa: E402

COMMAND_BOUNDARY_PREFIX = r"(?:^|[;&|`(]\s*)"

SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL = "CLAUDE_HEADLESS_SANCTIONED=1"

PROHIBITED_BASH_COMMAND_PATTERNS = [
    (
        rf"{COMMAND_BOUNDARY_PREFIX}git\s+add\s+(-A|--all|\.)(\s|$)",
        "git add -A/--all/. is prohibited; stage specific files (parallel work risk).",
    ),
    (
        rf"{COMMAND_BOUNDARY_PREFIX}(?:git|gh\s+repo)\s+clone\s+\S*castrozan[/-]?\.?dotfiles",
        "Cloning castrozan/.dotfiles is prohibited; use 'gh api' for remote access.",
    ),
    (
        rf"{COMMAND_BOUNDARY_PREFIX}direnv\s+(allow|hook|exec|reload|status|edit|deny|block|prune|version)\b",
        "direnv is prohibited; use 'devenv shell' or 'devenv shell -- command'.",
    ),
    (
        rf"{COMMAND_BOUNDARY_PREFIX}herdr\s+agent\s+start\b(?:(?!\s--tab(?=[\s=]))(?!\s--\s)[^;&|\n])*(?:$|[;&|\n]|\s--\s)",
        "herdr agent start without --tab splits an active tab someone is "
        "already working in; --workspace alone is not a pin because it only "
        "chooses which workspace's active tab gets split. Pin the exact tab: "
        '--tab "$HERDR_TAB_ID" --no-focus for your own, or create a fresh one '
        "with 'herdr tab create --workspace <id> --no-focus' and pass its id.",
    ),
    (
        rf"{COMMAND_BOUNDARY_PREFIX}claude(?![\w-])[^;&|`)\n]*?\s(?:-p|--print)(?:[=\s'\"]|$)",
        "claude -p/--print (headless oneshot) is prohibited; drive an interactive "
        "session instead (the claude-workspace wrapper, or a herdr agent via "
        '\'herdr agent start <name> --cwd <dir> --tab "$HERDR_TAB_ID" --no-focus '
        "-- claude'). "
        "For a genuinely sanctioned one-off, prefix the command with "
        f"{SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL}.",
        SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL,
    ),
]

PROHIBITED_FILE_PATH_PATTERNS = [
    (
        r"(?:^|/)castrozan/\.?dotfiles(?:/|$)",
        "Writing under castrozan/.dotfiles is prohibited; repo must not live on disk.",
    ),
]

PROHIBITED_PATTERNS_BY_TOOL = {
    "Bash": PROHIBITED_BASH_COMMAND_PATTERNS,
    "Write": PROHIBITED_FILE_PATH_PATTERNS,
    "Edit": PROHIBITED_FILE_PATH_PATTERNS,
    "NotebookEdit": PROHIBITED_FILE_PATH_PATTERNS,
}


def extract_inspectable_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return tool_input.get("command", "") or ""
    if tool_name in ("Write", "Edit"):
        return tool_input.get("file_path", "") or ""
    if tool_name == "NotebookEdit":
        return (
            tool_input.get("notebook_path", "") or tool_input.get("file_path", "") or ""
        )
    return ""


def find_first_violation(tool_name: str, inspectable_text: str):
    if not inspectable_text:
        return None

    patterns_for_this_tool = PROHIBITED_PATTERNS_BY_TOOL.get(tool_name, [])

    for rule in patterns_for_this_tool:
        pattern, reason = rule[0], rule[1]
        override_sentinel = rule[2] if len(rule) > 2 else None
        if not re.search(pattern, inspectable_text, re.IGNORECASE):
            continue
        if override_sentinel and override_sentinel in inspectable_text:
            continue
        return pattern, reason
    return None


def emit_block_and_exit(reason: str, tool_name: str, inspectable_text: str) -> None:
    deny_pre_tool_use_call(
        f"BLOCKED ({tool_name}): {reason}\nOffending input: {inspectable_text.strip()}"
    )


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    data = normalize_codex_tool_payload(data)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    inspectable_text = extract_inspectable_text(tool_name, tool_input)
    violation = find_first_violation(tool_name, inspectable_text)

    if violation is None:
        sys.exit(0)

    _pattern, reason = violation
    emit_block_and_exit(reason, tool_name, inspectable_text)


if __name__ == "__main__":
    main()
