"""Run external commands with a bounded timeout for context gathering."""

from __future__ import annotations

import subprocess


def run_cmd(args: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""
