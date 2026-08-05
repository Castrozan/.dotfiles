#!/usr/bin/env python3

from __future__ import annotations

import sys
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

POST_COMPACTION_RECOVERY_DIRECTIVE = (
    "POST-COMPACTION RECOVERY: the conversation was just summarized, so re-read any "
    "active HEARTBEAT.md or .deep-work/*/PLAN.md tracker on disk and restore the durable "
    "state before continuing: the deep-work path and plan phase, the user's requirements, "
    "the files already modified, the test and rebuild results, the key decisions, and the "
    "pre-work git SHA. Verbose tool outputs and raw research dumps are droppable; do not "
    "reconstruct them."
)


def handle(hook_input: dict):
    if hook_input.get("source", "") != "compact":
        return None
    return HandlerResult(additional_context=POST_COMPACTION_RECOVERY_DIRECTIVE)
