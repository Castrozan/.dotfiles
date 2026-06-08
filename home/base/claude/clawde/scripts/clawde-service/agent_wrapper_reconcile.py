import os
import re
import signal
import subprocess

AGENT_WRAPPER_PROCESS_MATCH_PATTERN = "agent-wrapper/wrapper.py --agent-name"
AGENT_NAME_ARGUMENT_PATTERN = re.compile(r"--agent-name (\S+)")
TMUX_SESSION_ARGUMENT_PATTERN = re.compile(r"--tmux-session (\S+)")


def read_process_command_line(process_id: int) -> str:
    result = subprocess.run(
        ["ps", "-ww", "-p", str(process_id), "-o", "command="],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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
        tmux_session_match = TMUX_SESSION_ARGUMENT_PATTERN.search(command_line)
        if not agent_name_match or not tmux_session_match:
            continue
        if tmux_session_match.group(1) != session_name:
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


def agent_names_with_running_wrapper_after_reconcile(
    session_name: str, declared_agent_names: set
) -> set:
    process_ids_by_agent_name = group_wrapper_process_ids_by_agent_name(
        find_session_agent_wrapper_processes(session_name)
    )
    terminate_duplicate_and_orphan_agent_wrappers(
        declared_agent_names, process_ids_by_agent_name
    )
    return set(process_ids_by_agent_name)
