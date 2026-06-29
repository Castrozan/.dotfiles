from __future__ import annotations

from pathlib import Path

import psutil

CHROME_GLOBAL_USER_DATA_DIRECTORY = str(Path.home() / ".config" / "chrome-global")


def joined_command_line_for_process(process) -> str:
    try:
        return " ".join(process.cmdline() or [])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def process_belongs_to_chrome_global(process) -> bool:
    return (
        f"--user-data-dir={CHROME_GLOBAL_USER_DATA_DIRECTORY}"
        in joined_command_line_for_process(process)
    )


def process_is_chrome_child(process) -> bool:
    return "--type=" in joined_command_line_for_process(process)


def find_chrome_global_processes() -> list:
    return [
        process
        for process in psutil.process_iter()
        if process_belongs_to_chrome_global(process)
    ]
