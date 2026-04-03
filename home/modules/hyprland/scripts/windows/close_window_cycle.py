import json
import os
import sys
from pathlib import Path

from hyprland_ipc import (
    get_active_window,
    run_hyprctl,
)

CLOSED_WINDOWS_HISTORY_FILE = (
    Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "hypr-closed-windows-history"
)
MAX_HISTORY_ENTRIES = 10


def read_process_cmdline(pid: int) -> str | None:
    try:
        raw_bytes = Path(f"/proc/{pid}/cmdline").read_bytes()
    except (FileNotFoundError, ProcessLookupError):
        return None
    return raw_bytes.replace(b"\x00", b" ").decode().strip()


def save_window_to_history(
    pid: int, window_class: str, workspace_id: int, title: str
) -> None:
    launch_command = read_process_cmdline(pid) if pid else None
    if not launch_command or not window_class:
        return

    entry = json.dumps(
        {
            "cmd": launch_command,
            "class": window_class,
            "workspace": workspace_id,
            "title": title,
        }
    )

    CLOSED_WINDOWS_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CLOSED_WINDOWS_HISTORY_FILE, "a") as history_file:
        history_file.write(entry + "\n")

    truncate_history_file_to_max_entries()


def truncate_history_file_to_max_entries() -> None:
    if not CLOSED_WINDOWS_HISTORY_FILE.exists():
        return
    lines = CLOSED_WINDOWS_HISTORY_FILE.read_text().splitlines()
    if len(lines) > MAX_HISTORY_ENTRIES:
        CLOSED_WINDOWS_HISTORY_FILE.write_text(
            "\n".join(lines[-MAX_HISTORY_ENTRIES:]) + "\n"
        )


def main() -> None:
    active_window = get_active_window()
    if not active_window:
        sys.exit(1)

    active_workspace_id = active_window.get("workspace", {}).get("id")
    active_class = active_window.get("class", "")
    active_title = active_window.get("title", "")
    active_pid = active_window.get("pid", 0)

    save_window_to_history(active_pid, active_class, active_workspace_id, active_title)

    run_hyprctl("dispatch", "killactive")


if __name__ == "__main__":
    main()
