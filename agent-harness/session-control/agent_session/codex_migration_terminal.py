import os
import re

from agent_session.codex_migration_contract import require


def inspect_terminal_descriptors(server_identifier, client_identifier):
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
    return {"server_stderr": server_stderr, "client_stderr": client_stderr}


def inspect_process_groups(process_info, identities):
    launcher_session = os.getsid(identities["launcher"])
    process_groups = {
        name: os.getpgid(identifier) for name, identifier in identities.items()
    }
    require(
        launcher_session == os.getsid(process_info["shell_pid"])
        and process_groups["launcher"] == process_info["foreground_process_group_id"],
        "replacement is not in its pane foreground session",
    )
    require(
        os.getsid(identities["server"]) == launcher_session
        and os.getsid(identities["client"]) == launcher_session,
        "replacement escaped pane session",
    )
    require(
        process_groups["server"] == identities["server"]
        and process_groups["server"] != process_groups["launcher"],
        "replacement backend process group mismatch",
    )
    require(
        process_groups["client"] == process_groups["launcher"],
        "replacement client foreground group mismatch",
    )
    return launcher_session, process_groups
