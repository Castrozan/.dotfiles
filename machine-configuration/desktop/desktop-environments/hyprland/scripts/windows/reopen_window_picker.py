import json
import os
import subprocess
import sys
from pathlib import Path

from hyprland_ipc import run_hyprctl

CLOSED_WINDOWS_HISTORY_FILE = (
    Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "hypr-closed-windows-history"
)


def load_history_entries() -> list[dict]:
    if not CLOSED_WINDOWS_HISTORY_FILE.exists():
        return []
    lines = CLOSED_WINDOWS_HISTORY_FILE.read_text().splitlines()
    entries = []
    for line in lines:
        if line.strip():
            entries.append(json.loads(line))
    return entries


def format_entry_for_display(entry: dict) -> str:
    workspace_id = entry.get("workspace", "?")
    title = entry.get("title", "unknown")
    return f"[{workspace_id}] {title}"


def run_fuzzel_picker(display_lines: list[str]) -> str | None:
    fuzzel_input = "\n".join(reversed(display_lines))
    result = subprocess.run(
        ["hypr-fuzzel", "--dmenu", "--prompt", "Reopen: "],
        input=fuzzel_input,
        capture_output=True,
        text=True,
    )
    selected = result.stdout.strip()
    return selected if selected else None


def remove_entry_from_history_by_line_number(line_number: int) -> None:
    lines = CLOSED_WINDOWS_HISTORY_FILE.read_text().splitlines()
    del lines[line_number]
    CLOSED_WINDOWS_HISTORY_FILE.write_text("\n".join(lines) + "\n" if lines else "")


def main() -> None:
    entries = load_history_entries()
    if not entries:
        sys.exit(0)

    display_lines = [format_entry_for_display(entry) for entry in entries]
    selected_display = run_fuzzel_picker(display_lines)
    if not selected_display:
        sys.exit(0)

    for index in range(len(entries) - 1, -1, -1):
        if display_lines[index] == selected_display:
            launch_command = entries[index].get("cmd")
            target_workspace_id = entries[index].get("workspace")
            if not launch_command:
                sys.exit(1)
            remove_entry_from_history_by_line_number(index)
            run_hyprctl(
                "dispatch",
                "exec",
                f"[workspace {target_workspace_id} silent] {launch_command}",
            )
            return

    sys.exit(1)


if __name__ == "__main__":
    main()
