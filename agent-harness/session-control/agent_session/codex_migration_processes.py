from pathlib import Path

from agent_session.codex_migration_contract import require, resume_arguments
from agent_session.codex_migration_connections import inspect_private_connection
from agent_session.codex_migration_terminal import (
    inspect_process_groups,
    inspect_terminal_descriptors,
)


def process_birth(process_identifier):
    try:
        fields = (
            Path(f"/proc/{process_identifier}/stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()
        )
        return {
            "start_ticks": int(fields[19]),
            "state": fields[0],
            "parent": int(fields[1]),
        }
    except FileNotFoundError:
        return None


def inspect_new_processes(process_info, pane, package, plan):
    _validate_resumed_pane(process_info, pane, plan)
    foreground = process_info["foreground_processes"]
    launcher = _matching_launcher(foreground, package, plan)
    client = _matching_client(foreground, plan)
    server_identifier, server_arguments = _private_server_process(launcher["pid"], plan)
    identities = {
        "launcher": launcher["pid"],
        "client": client["pid"],
        "server": server_identifier,
    }
    births = _inspect_owned_births(identities)
    _validate_process_executables(identities, package, plan)
    launcher_session, process_groups = inspect_process_groups(process_info, identities)
    descriptors = inspect_terminal_descriptors(server_identifier, client["pid"])
    client_arguments = (
        Path(f"/proc/{client['pid']}/cmdline")
        .read_bytes()
        .decode()
        .strip("\0")
        .split("\0")
    )
    require(client_arguments == client["argv"], "new client arguments changed")
    connection = inspect_private_connection(server_arguments, client_arguments)
    _validate_replacement_births(identities, births)
    return {
        "session_id": launcher_session,
        "process_groups": process_groups,
        "pids": identities,
        "births": births,
        **descriptors,
        **connection,
    }


def _validate_resumed_pane(process_info, pane, plan):
    require(
        process_info["pane_id"] == plan["pane_identifier"]
        and pane["pane_id"] == plan["pane_identifier"],
        "inspection pane mismatch",
    )
    session = pane.get("agent_session") or {}
    if session.get("value") is None:
        raise LookupError("recorded resumed thread is not available")
    require(
        session.get("value") == plan["thread_identifier"]
        and session.get("agent") == "codex",
        "resumed thread mismatch",
    )


def _matching_launcher(foreground, package, plan):
    expected = [package["python"], package["launch_script"], *resume_arguments(plan)]
    return _unique_foreground_process(
        [process for process in foreground if process.get("argv", []) == expected]
    )


def _matching_client(foreground, plan):
    return _unique_foreground_process(
        [process for process in foreground if _client_matches_resume(process, plan)]
    )


def _client_matches_resume(process, plan):
    arguments = process.get("argv", [])
    return (
        arguments[:2] == [plan["upstream_binary"], "--remote"]
        and arguments[3:] == resume_arguments(plan)[4:]
    )


def _unique_foreground_process(processes):
    if len(processes) != 1:
        raise LookupError(
            "exact new launcher and resumed terminal client are not available"
        )
    return processes[0]


def _private_server_process(launcher_identifier, plan):
    children = (
        Path(f"/proc/{launcher_identifier}/task/{launcher_identifier}/children")
        .read_text()
        .split()
    )
    servers = []
    for child in children:
        arguments = _read_child_arguments(child)
        if _is_private_server(arguments, plan["upstream_binary"]):
            servers.append((int(child), arguments))
    if len(servers) != 1:
        raise LookupError("unique direct-child private server is not available")
    return servers[0]


def _read_child_arguments(child):
    try:
        return (
            Path(f"/proc/{child}/cmdline").read_bytes().decode().strip("\0").split("\0")
        )
    except FileNotFoundError:
        return None


def _is_private_server(arguments, upstream_binary):
    return arguments and arguments[0] == upstream_binary and "app-server" in arguments


def _inspect_owned_births(identities):
    births = {
        name: process_birth(identifier) for name, identifier in identities.items()
    }
    require(
        all(birth and birth["state"] != "Z" for birth in births.values()),
        "new process disappeared",
    )
    require(
        births["server"]["parent"] == identities["launcher"]
        and births["client"]["parent"] == identities["launcher"],
        "new child ownership mismatch",
    )
    return births


def _validate_process_executables(identities, package, plan):
    for identifier in (identities["server"], identities["client"]):
        require(
            Path(f"/proc/{identifier}/exe").resolve()
            == Path(plan["upstream_binary"]).resolve(),
            "new upstream executable mismatch",
        )
    require(
        Path(f"/proc/{identities['launcher']}/exe").resolve()
        == Path(package["python"]).resolve(),
        "new launcher executable mismatch",
    )


def _validate_replacement_births(identities, births):
    require(
        all(
            (observed := process_birth(identifier))
            and observed["start_ticks"] == births[name]["start_ticks"]
            and observed["parent"] == births[name]["parent"]
            and observed["state"] != "Z"
            for name, identifier in identities.items()
        ),
        "replacement birth changed during inspection",
    )
