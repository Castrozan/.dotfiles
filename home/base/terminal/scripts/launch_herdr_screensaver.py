import json
import shutil
import subprocess
import sys

SCREENSAVER_WORKSPACE_LABEL = "screensaver"
PRIMARY_LEFT_COLUMN_RATIO = 0.66
RIGHT_COLUMN_VERTICAL_SPLIT_RATIO = 0.60
PRECOMPUTE_LOOP_CAPTURE_SECONDS = 60
PRECOMPUTE_LOOP_WRAPPED_COMMAND_MARKERS = ("equation-art",)


def run_herdr(*arguments):
    return subprocess.run(
        ["herdr", *arguments],
        capture_output=True,
        text=True,
        check=True,
    )


def run_herdr_json(*arguments):
    completed = run_herdr(*arguments)
    return json.loads(completed.stdout)


def split_command_into_segments(command):
    segments = [command]
    for separator in (";", "&&", "||", "|", "&"):
        expanded = []
        for segment in segments:
            expanded.extend(segment.split(separator))
        segments = expanded
    return [segment.strip() for segment in segments if segment.strip()]


def all_command_segments_available(command):
    for segment in split_command_into_segments(command):
        executable = segment.split()[0]
        if not shutil.which(executable):
            return False
    return True


def resolve_available_screensaver_commands():
    if shutil.which("cbonsai"):
        companion_command = "cbonsai --live --infinite"
    else:
        companion_command = "cmatrix -b -s -u 8"
    candidate_commands = [
        "equation-art",
        companion_command,
        "cmatrix -b -u 8",
        "sleep 3; bad-apple",
    ]
    return [
        command
        for command in candidate_commands
        if all_command_segments_available(command)
    ]


def wrap_command_for_cheap_replay(command):
    if not shutil.which("precompute-loop"):
        return command
    if not any(marker in command for marker in PRECOMPUTE_LOOP_WRAPPED_COMMAND_MARKERS):
        return command
    return f"precompute-loop --seconds {PRECOMPUTE_LOOP_CAPTURE_SECONDS} -- {command}"


def find_screensaver_workspace_id():
    listing = run_herdr_json("workspace", "list")
    for workspace in listing["result"]["workspaces"]:
        if workspace["label"] == SCREENSAVER_WORKSPACE_LABEL:
            return workspace["workspace_id"]
    return None


def list_workspace_pane_ids(workspace_id):
    listing = run_herdr_json("pane", "list", "--workspace", workspace_id)
    return [pane["pane_id"] for pane in listing["result"]["panes"]]


def pane_is_running_foreground_process(pane_id):
    info = run_herdr_json("pane", "process-info", "--pane", pane_id)
    process_info = info["result"]["process_info"]
    return process_info["foreground_process_group_id"] != process_info["shell_pid"]


def workspace_has_running_screensaver(workspace_id):
    return any(
        pane_is_running_foreground_process(pane_id)
        for pane_id in list_workspace_pane_ids(workspace_id)
    )


def create_screensaver_workspace():
    created = run_herdr_json(
        "workspace", "create", "--label", SCREENSAVER_WORKSPACE_LABEL, "--no-focus"
    )
    return (
        created["result"]["workspace"]["workspace_id"],
        created["result"]["root_pane"]["pane_id"],
    )


def split_pane(pane_id, direction, original_pane_ratio):
    split = run_herdr_json(
        "pane",
        "split",
        pane_id,
        "--direction",
        direction,
        "--ratio",
        str(original_pane_ratio),
        "--no-focus",
    )
    return split["result"]["pane"]["pane_id"]


def build_screensaver_panes(root_pane_id, command_count):
    panes = [root_pane_id]
    if command_count >= 2:
        right_column_pane = split_pane(root_pane_id, "right", PRIMARY_LEFT_COLUMN_RATIO)
        panes.append(right_column_pane)
        if command_count >= 3:
            bottom_right_pane = split_pane(
                right_column_pane, "down", RIGHT_COLUMN_VERTICAL_SPLIT_RATIO
            )
            panes.append(bottom_right_pane)
    return panes


def start_screensaver():
    commands = resolve_available_screensaver_commands()
    if not commands:
        return
    workspace_id, root_pane_id = create_screensaver_workspace()
    panes = build_screensaver_panes(root_pane_id, len(commands))
    for pane_id, command in zip(panes, commands):
        run_herdr("pane", "run", pane_id, wrap_command_for_cheap_replay(command))
    run_herdr("workspace", "focus", workspace_id)


def main():
    if not shutil.which("herdr"):
        return 0
    try:
        existing_workspace_id = find_screensaver_workspace_id()
        if existing_workspace_id is not None:
            if workspace_has_running_screensaver(existing_workspace_id):
                run_herdr("workspace", "focus", existing_workspace_id)
                return 0
            run_herdr("workspace", "close", existing_workspace_id)
        start_screensaver()
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as error:
        message = f"herdr-screensaver: {error}"
        captured_stderr = getattr(error, "stderr", None)
        if captured_stderr:
            message = f"{message}\n{captured_stderr.strip()}"
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
