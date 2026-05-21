from __future__ import annotations

import json
import sys
from pathlib import Path


def read_hook_input_from_stdin() -> dict:
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return {}


def format_recall_context(recall_paths: list[Path], memory_directory: Path) -> str:
    relative_paths = [
        f"@{path.resolve().relative_to(memory_directory.parent.parent.parent)}"
        if memory_directory.parent.parent.parent in path.resolve().parents
        else f"@{path}"
        for path in recall_paths
    ]
    return "Recall: " + " ".join(relative_paths)


def emit_additional_context_and_exit(additional_context: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": additional_context,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def exit_silently() -> None:
    sys.exit(0)
