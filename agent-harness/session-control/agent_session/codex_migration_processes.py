import os
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def resume_arguments(plan):
    return [
        "--sandbox",
        "danger-full-access",
        "--ask-for-approval",
        "never",
        "--profile",
        "dotfiles-interactive",
        "resume",
        plan["thread_identifier"],
    ]


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
    foreground = process_info["foreground_processes"]
    launchers = [
        process
        for process in foreground
        if process.get("argv", [])
        == [package["python"], package["launch_script"], *resume_arguments(plan)]
    ]
    clients = [
        process
        for process in foreground
        if process.get("argv", [])[:2] == [plan["upstream_binary"], "--remote"]
        and process["argv"][3:] == resume_arguments(plan)[4:]
    ]
    if len(launchers) != 1 or len(clients) != 1:
        raise LookupError(
            "exact new launcher and resumed terminal client are not available"
        )
    launcher_identifier, client_identifier = launchers[0]["pid"], clients[0]["pid"]
    children = (
        Path(f"/proc/{launcher_identifier}/task/{launcher_identifier}/children")
        .read_text()
        .split()
    )
    servers = []
    for child in children:
        try:
            arguments = (
                Path(f"/proc/{child}/cmdline")
                .read_bytes()
                .decode()
                .strip("\0")
                .split("\0")
            )
        except FileNotFoundError:
            continue
        if (
            arguments
            and arguments[0] == plan["upstream_binary"]
            and "app-server" in arguments
        ):
            servers.append((int(child), arguments))
    if len(servers) != 1:
        raise LookupError("unique direct-child private server is not available")
    server_identifier, server_arguments = servers[0]
    identities = {
        "launcher": launcher_identifier,
        "client": client_identifier,
        "server": server_identifier,
    }
    births = {
        name: process_birth(identifier) for name, identifier in identities.items()
    }
    require(
        all(birth and birth["state"] != "Z" for birth in births.values()),
        "new process disappeared",
    )
    require(
        births["server"]["parent"] == launcher_identifier
        and births["client"]["parent"] == launcher_identifier,
        "new child ownership mismatch",
    )
    for identifier in (server_identifier, client_identifier):
        require(
            Path(f"/proc/{identifier}/exe").resolve()
            == Path(plan["upstream_binary"]).resolve(),
            "new upstream executable mismatch",
        )
    require(
        Path(f"/proc/{launcher_identifier}/exe").resolve()
        == Path(package["python"]).resolve(),
        "new launcher executable mismatch",
    )
    launcher_session = os.getsid(launcher_identifier)
    process_groups = {
        name: os.getpgid(identifier) for name, identifier in identities.items()
    }
    require(
        launcher_session == os.getsid(process_info["shell_pid"])
        and process_groups["launcher"] == process_info["foreground_process_group_id"],
        "replacement is not in its pane foreground session",
    )
    require(
        os.getsid(server_identifier) == launcher_session
        and os.getsid(client_identifier) == launcher_session,
        "replacement escaped pane session",
    )
    require(
        process_groups["server"] == server_identifier
        and process_groups["server"] != process_groups["launcher"],
        "replacement backend process group mismatch",
    )
    require(
        process_groups["client"] == process_groups["launcher"],
        "replacement client foreground group mismatch",
    )
    server_stderr = os.readlink(f"/proc/{server_identifier}/fd/2")
    client_stderr = os.readlink(f"/proc/{client_identifier}/fd/2")
    require(
        re.fullmatch(r"pipe:\[\d+\]", server_stderr),
        "private server stderr is not a pipe",
    )
    require(
        re.fullmatch(r"/dev/pts/\d+", client_stderr),
        "terminal client stderr is not its PTY",
    )
    require(
        os.readlink(f"/proc/{client_identifier}/fd/0") == client_stderr
        and os.readlink(f"/proc/{client_identifier}/fd/1") == client_stderr,
        "terminal client descriptors do not share its PTY",
    )
    endpoint = server_arguments[server_arguments.index("--listen") + 1]
    require(
        endpoint.startswith("unix:///tmp/codex-session-"),
        "private socket endpoint mismatch",
    )
    socket_path = Path(endpoint.removeprefix("unix://"))
    require(socket_path.is_socket(), "private server socket unavailable")
    sizes = {}
    for name in ("server-stderr.log", "server-stderr.previous.log"):
        path = socket_path.parent / name
        sizes[name] = path.stat().st_size if path.exists() else 0
        require(sizes[name] <= 1024 * 1024, "diagnostic file exceeded 1 MiB")
    require(
        sum(sizes.values()) <= 2 * 1024 * 1024, "session diagnostics exceeded 2 MiB"
    )
    require(
        all(
            process_birth(identifier) == births[name]
            for name, identifier in identities.items()
        ),
        "replacement birth changed during inspection",
    )
    return {
        "session_id": launcher_session,
        "process_groups": process_groups,
        "pids": identities,
        "births": births,
        "server_stderr": server_stderr,
        "client_stderr": client_stderr,
        "socket_directory": str(socket_path.parent),
        "diagnostic_sizes": sizes,
    }
