"""Linter availability detection and invocation for the lint-on-edit hook."""

from __future__ import annotations

import os
import subprocess


def is_linter_executable_available_in_path(linter_cmd: list[str]) -> bool:
    try:
        subprocess.run([linter_cmd[0], "--version"], capture_output=True, timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run([linter_cmd[0], "--help"], capture_output=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def run_linter_on_file(file_path: str, linter: dict) -> list[str]:
    cmd = linter["cmd"] + [file_path]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(file_path) or ".",
        )
        combined_stdout_and_stderr_output = result.stdout + result.stderr
        issues = linter["parse"](combined_stdout_and_stderr_output)
        return [issue for issue in issues if issue.strip()]
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []
