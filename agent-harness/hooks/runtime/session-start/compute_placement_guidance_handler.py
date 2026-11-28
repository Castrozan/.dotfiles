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
from session_context_command_runner import run_cmd  # noqa: E402

GUIDANCE_COMMAND = ["agent-api", "directives", "--guidance"]
GUIDANCE_TIMEOUT_SECONDS = 2


def handle(hook_input: dict):
    exit_code, guidance = run_cmd(GUIDANCE_COMMAND, timeout=GUIDANCE_TIMEOUT_SECONDS)
    if exit_code != 0 or not guidance:
        return None
    return HandlerResult(additional_context=guidance)
