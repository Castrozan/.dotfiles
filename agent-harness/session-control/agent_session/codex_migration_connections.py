from pathlib import Path

from agent_session.codex_migration_contract import require


def inspect_private_connection(server_arguments, client_arguments):
    endpoint = server_arguments[server_arguments.index("--listen") + 1]
    require(
        endpoint.startswith("unix:///tmp/codex-session-"),
        "private socket endpoint mismatch",
    )
    server_path = Path(endpoint.removeprefix("unix://"))
    require(
        server_path.name == "server.sock" and server_path.is_socket(),
        "private server socket unavailable",
    )
    remote = client_arguments[2]
    require(remote.startswith("unix://"), "client remote is not a Unix socket")
    client_path = Path(remote.removeprefix("unix://"))
    require(
        client_path.is_absolute()
        and client_path.name in {"server.sock", "client.sock"}
        and client_path.resolve().parent == server_path.resolve().parent
        and client_path.is_socket(),
        "client remote is not an existing declared private socket",
    )
    sizes = {}
    for name in ("server-stderr.log", "server-stderr.previous.log"):
        path = server_path.parent / name
        sizes[name] = path.stat().st_size if path.exists() else 0
        require(sizes[name] <= 1024 * 1024, "diagnostic file exceeded 1 MiB")
    require(
        sum(sizes.values()) <= 2 * 1024 * 1024, "session diagnostics exceeded 2 MiB"
    )
    return {
        "server_socket": str(server_path.resolve()),
        "client_socket": str(client_path.resolve()),
        "client_endpoint": remote,
        "socket_directory": str(server_path.parent),
        "diagnostic_sizes": sizes,
    }
