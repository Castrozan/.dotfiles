import json
import os
import sys
from pathlib import Path

from hyprland_ipc import run_hyprctl

CLOSED_WINDOWS_HISTORY_FILE = (
    Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "hypr-closed-windows-history"
)


def main() -> None:
    if not CLOSED_WINDOWS_HISTORY_FILE.exists():
        sys.exit(0)

    lines = CLOSED_WINDOWS_HISTORY_FILE.read_text().splitlines()
    if not lines:
        sys.exit(0)

    last_entry = json.loads(lines[-1])
    launch_command = last_entry.get("cmd")
    target_workspace_id = last_entry.get("workspace")

    if not launch_command:
        sys.exit(1)

    CLOSED_WINDOWS_HISTORY_FILE.write_text(
        "\n".join(lines[:-1]) + "\n" if lines[:-1] else ""
    )

    run_hyprctl(
        "dispatch",
        "exec",
        f"[workspace {target_workspace_id} silent] {launch_command}",
    )


if __name__ == "__main__":
    main()
