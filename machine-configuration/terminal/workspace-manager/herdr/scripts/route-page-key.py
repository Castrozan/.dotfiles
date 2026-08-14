"""Route Ctrl+Page keys between the focused pane's editor and herdr tab switching.

herdr binds ctrl+pageup and ctrl+pagedown, so nvim never sees them on its own.
This router gives them back whenever nvim owns the focused pane and switches the
herdr tab otherwise. prefix+pageup and prefix+pagedown stay the escape hatch that
switches tabs from inside nvim.
"""

import json
import os
import subprocess
import sys

EDITOR_PROCESS_NAMES = frozenset({"nvim"})

KEY_BY_DIRECTION = {"previous": "ctrl+pageup", "next": "ctrl+pagedown"}

HERDR_CALL_TIMEOUT_SECONDS = 2


def herdr_binary_path():
    return os.environ.get("HERDR_BIN_PATH") or "herdr"


def run_herdr(arguments):
    """Run one herdr CLI command and return its parsed response, or None on failure."""
    try:
        completed = subprocess.run(
            [herdr_binary_path(), *arguments],
            capture_output=True,
            text=True,
            timeout=HERDR_CALL_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    try:
        response = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    return response if isinstance(response, dict) else None


def herdr_result(arguments, result_key):
    """Return one field of a herdr CLI JSON result, or None when the call fails."""
    response = run_herdr(arguments)
    if response is None:
        return None
    return response.get("result", {}).get(result_key)


def foreground_process_names(process_info):
    """Collect every foreground process name in the pane, lowercased and unqualified."""
    names = set()
    for process in process_info.get("foreground_processes", []):
        for reported_name in (process.get("name"), process.get("argv0")):
            if reported_name:
                names.add(os.path.basename(reported_name).lower())
    return names


def pane_is_owned_by_editor(process_names):
    return bool(process_names & EDITOR_PROCESS_NAMES)


def neighbor_tab_id(tabs, workspace_id, direction):
    """Return the tab that wins the key, wrapping at both ends of the workspace."""
    workspace_tabs = [tab for tab in tabs if tab.get("workspace_id") == workspace_id]
    if len(workspace_tabs) < 2:
        return None
    focused_index = next(
        (index for index, tab in enumerate(workspace_tabs) if tab.get("focused")),
        None,
    )
    if focused_index is None:
        return None
    step = -1 if direction == "previous" else 1
    neighbor = workspace_tabs[(focused_index + step) % len(workspace_tabs)]
    return neighbor.get("tab_id")


def send_key_to_pane(pane_id, key):
    herdr_result(["pane", "send-keys", pane_id, key], "unused")
    return 0


def focus_neighbor_tab(workspace_id, direction):
    tabs = herdr_result(["tab", "list", "--workspace", workspace_id], "tabs")
    if not tabs:
        return 0
    target_tab_id = neighbor_tab_id(tabs, workspace_id, direction)
    if target_tab_id is None:
        return 0
    herdr_result(["tab", "focus", target_tab_id], "unused")
    return 0


def main(argv):
    if len(argv) != 2 or argv[1] not in KEY_BY_DIRECTION:
        print(f"usage: {argv[0]} {'|'.join(KEY_BY_DIRECTION)}", file=sys.stderr)
        return 2

    direction = argv[1]
    pane_id = os.environ.get("HERDR_ACTIVE_PANE_ID", "")
    workspace_id = os.environ.get("HERDR_ACTIVE_WORKSPACE_ID", "")
    if not pane_id:
        return 0

    process_info = herdr_result(
        ["pane", "process-info", "--pane", pane_id], "process_info"
    )
    # An unreadable pane keeps today's behavior: the key goes to whatever runs there.
    if process_info is None or pane_is_owned_by_editor(
        foreground_process_names(process_info)
    ):
        return send_key_to_pane(pane_id, KEY_BY_DIRECTION[direction])

    if not workspace_id:
        return 0
    return focus_neighbor_tab(workspace_id, direction)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
