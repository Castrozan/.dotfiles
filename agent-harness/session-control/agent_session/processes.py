import os
import signal
import subprocess
import time

from . import restart_lock


def process_info_for(process_identifier: int) -> tuple[int, str] | None:
    parent_process = subprocess.run(
        ["ps", "-p", str(process_identifier), "-o", "ppid="],
        capture_output=True,
        text=True,
        check=False,
    )
    command_process = subprocess.run(
        ["ps", "-ww", "-p", str(process_identifier), "-o", "command="],
        capture_output=True,
        text=True,
        check=False,
    )
    if parent_process.returncode != 0 or command_process.returncode != 0:
        return None
    try:
        parent_process_identifier = int(parent_process.stdout.strip())
    except ValueError:
        return None
    return parent_process_identifier, command_process.stdout.strip()


def process_is_descendant_of(
    process_identifier: int, ancestor_process_identifier: int
) -> bool:
    current_process_identifier = process_identifier
    while current_process_identifier not in {0, 1}:
        if current_process_identifier == ancestor_process_identifier:
            return True
        process_information = process_info_for(current_process_identifier)
        if process_information is None:
            return False
        parent_process_identifier, _command_line = process_information
        if parent_process_identifier == current_process_identifier:
            return False
        current_process_identifier = parent_process_identifier
    return False


def clawde_wrapper_is_ancestor_of(starting_process_identifier: int) -> bool:
    current_process_identifier = starting_process_identifier
    while current_process_identifier not in {0, 1}:
        process_information = process_info_for(current_process_identifier)
        if process_information is None:
            return False
        parent_process_identifier, command_line = process_information
        if (
            "wrapper.py" in command_line
            and "--agent-name" in command_line
            and "--config-file" in command_line
        ):
            return True
        if parent_process_identifier == current_process_identifier:
            return False
        current_process_identifier = parent_process_identifier
    return False


def child_process_identifiers_for(process_identifier: int) -> list[int]:
    completed_process = subprocess.run(
        ["pgrep", "-P", str(process_identifier)],
        capture_output=True,
        text=True,
        check=False,
    )
    return [
        int(child_process_identifier)
        for child_process_identifier in completed_process.stdout.splitlines()
        if child_process_identifier.isdecimal()
    ]


def descendant_process_identifiers_for(process_identifier: int) -> list[int]:
    descendant_process_identifiers = []
    for child_process_identifier in child_process_identifiers_for(process_identifier):
        descendant_process_identifiers.extend(
            descendant_process_identifiers_for(child_process_identifier)
        )
        descendant_process_identifiers.append(child_process_identifier)
    return descendant_process_identifiers


def signal_process(process_identifier: int, signal_number: int) -> None:
    try:
        os.kill(process_identifier, signal_number)
    except ProcessLookupError:
        return


def terminate_agent_session(
    process_identifier: int,
    excluded_process_identifiers: frozenset[int] = frozenset(),
) -> None:
    descendant_process_identifiers = descendant_process_identifiers_for(
        process_identifier
    )
    terminable_descendant_process_identifiers = [
        descendant_process_identifier
        for descendant_process_identifier in descendant_process_identifiers
        if descendant_process_identifier not in excluded_process_identifiers
    ]
    for descendant_process_identifier in terminable_descendant_process_identifiers:
        signal_process(descendant_process_identifier, signal.SIGTERM)
    signal_process(process_identifier, signal.SIGTERM)
    time.sleep(0.5)
    for descendant_process_identifier in terminable_descendant_process_identifiers:
        signal_process(descendant_process_identifier, signal.SIGKILL)


def process_is_running(process_identifier: int) -> bool:
    try:
        os.kill(process_identifier, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_for_agent_session_exit(process_identifier: int) -> bool:
    deadline = time.monotonic() + restart_lock.RESTART_WAIT_SECONDS
    while process_is_running(process_identifier):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.2)
    return True
