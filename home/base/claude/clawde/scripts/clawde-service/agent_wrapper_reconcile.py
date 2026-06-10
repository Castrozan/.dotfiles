import json
import os
import re
import signal
import subprocess

AGENT_WRAPPER_PROCESS_MATCH_PATTERN = "agent-wrapper/wrapper.py --agent-name"
AGENT_NAME_ARGUMENT_PATTERN = re.compile(r"--agent-name (\S+)")
CONFIG_FILE_ARGUMENT_PATTERN = re.compile(r"--config-file (\S+)")


def read_process_command_line(process_id: int) -> str:
    result = subprocess.run(
        ["ps", "-ww", "-p", str(process_id), "-o", "command="],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def read_tmux_session_from_launch_config(config_file_path: str) -> str | None:
    try:
        with open(config_file_path) as config_file:
            return json.load(config_file).get("tmux_session")
    except (OSError, ValueError):
        return None


def find_session_agent_wrapper_processes(session_name: str) -> list[dict]:
    pgrep_result = subprocess.run(
        ["pgrep", "-f", AGENT_WRAPPER_PROCESS_MATCH_PATTERN],
        capture_output=True,
        text=True,
    )
    wrapper_processes = []
    for line in pgrep_result.stdout.split():
        if not line.strip().isdigit():
            continue
        process_id = int(line)
        command_line = read_process_command_line(process_id)
        agent_name_match = AGENT_NAME_ARGUMENT_PATTERN.search(command_line)
        config_file_match = CONFIG_FILE_ARGUMENT_PATTERN.search(command_line)
        if not agent_name_match or not config_file_match:
            continue
        if (
            read_tmux_session_from_launch_config(config_file_match.group(1))
            != session_name
        ):
            continue
        wrapper_processes.append(
            {"process_id": process_id, "agent_name": agent_name_match.group(1)}
        )
    return wrapper_processes


def terminate_agent_wrapper_process(process_id: int) -> None:
    try:
        os.kill(process_id, signal.SIGTERM)
    except ProcessLookupError:
        pass


def group_wrapper_process_ids_by_agent_name(wrapper_processes: list[dict]) -> dict:
    process_ids_by_agent_name: dict = {}
    for wrapper_process in wrapper_processes:
        process_ids_by_agent_name.setdefault(wrapper_process["agent_name"], []).append(
            wrapper_process["process_id"]
        )
    return process_ids_by_agent_name


def terminate_duplicate_and_orphan_agent_wrappers(
    declared_agent_names: set, process_ids_by_agent_name: dict
) -> None:
    for agent_name, process_ids in process_ids_by_agent_name.items():
        ordered_process_ids = sorted(process_ids)
        if agent_name in declared_agent_names:
            doomed_process_ids = ordered_process_ids[1:]
        else:
            doomed_process_ids = ordered_process_ids
        for process_id in doomed_process_ids:
            terminate_agent_wrapper_process(process_id)


def surviving_wrapper_process_id_by_agent_name(
    declared_agent_names: set, process_ids_by_agent_name: dict
) -> dict:
    surviving_process_id_by_agent_name = {}
    for agent_name, process_ids in process_ids_by_agent_name.items():
        if agent_name not in declared_agent_names:
            continue
        surviving_process_id_by_agent_name[agent_name] = min(process_ids)
    return surviving_process_id_by_agent_name


def find_session_window_panes(session_name: str) -> list[dict]:
    result = subprocess.run(
        [
            "tmux",
            "list-panes",
            "-s",
            "-t",
            session_name,
            "-F",
            "#{window_id} #{window_name} #{pane_pid}",
        ],
        capture_output=True,
        text=True,
    )
    window_panes = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3 or not fields[2].isdigit():
            continue
        window_panes.append(
            {
                "window_id": fields[0],
                "window_name": fields[1],
                "pane_pid": int(fields[2]),
            }
        )
    return window_panes


def rename_window(window_id: str, window_name: str) -> None:
    subprocess.run(
        ["tmux", "rename-window", "-t", window_id, window_name],
        capture_output=True,
        text=True,
    )


def rename_windows_to_match_running_wrapper_identity(
    session_name: str, agent_name_by_wrapper_process_id: dict
) -> None:
    for window_pane in find_session_window_panes(session_name):
        agent_name = agent_name_by_wrapper_process_id.get(window_pane["pane_pid"])
        if agent_name is None:
            continue
        if window_pane["window_name"] == agent_name:
            continue
        rename_window(window_pane["window_id"], agent_name)


def agent_names_with_running_wrapper_after_reconcile(
    session_name: str, declared_agent_names: set
) -> set:
    process_ids_by_agent_name = group_wrapper_process_ids_by_agent_name(
        find_session_agent_wrapper_processes(session_name)
    )
    terminate_duplicate_and_orphan_agent_wrappers(
        declared_agent_names, process_ids_by_agent_name
    )
    surviving_process_id_by_agent_name = surviving_wrapper_process_id_by_agent_name(
        declared_agent_names, process_ids_by_agent_name
    )
    rename_windows_to_match_running_wrapper_identity(
        session_name,
        {
            process_id: agent_name
            for agent_name, process_id in surviving_process_id_by_agent_name.items()
        },
    )
    return set(surviving_process_id_by_agent_name)
