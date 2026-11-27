from __future__ import annotations

import os
import shutil
import subprocess

from hook_dispatch import HandlerResult, requested_hook_surface

REX_BLOCK_ENVIRONMENT_VARIABLE = "REX_BLOCK"
REX_CONTEXT_TIMEOUT_SECONDS = 3


def rex_session_start_command(rex_executable: str, agent_name: str) -> list[str]:
    return [
        rex_executable,
        "__internal",
        "session-start",
        f"--agent={agent_name}",
        "--feature-session-naming=false",
        "--autostart=false",
        f"--timeout={REX_CONTEXT_TIMEOUT_SECONDS}s",
    ]


def handle(hook_input: dict):
    if not os.environ.get(REX_BLOCK_ENVIRONMENT_VARIABLE):
        return None
    rex_executable = shutil.which("rex")
    if rex_executable is None:
        return None
    try:
        completed = subprocess.run(
            rex_session_start_command(rex_executable, requested_hook_surface()),
            capture_output=True,
            text=True,
            timeout=REX_CONTEXT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return HandlerResult(additional_context=completed.stdout.strip())
