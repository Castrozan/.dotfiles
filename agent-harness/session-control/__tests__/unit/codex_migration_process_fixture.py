from contextlib import contextmanager
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace

from agent_session import codex_migration_processes as processes
from agent_session.codex_migration_contract import resume_arguments


@contextmanager
def prepare_process_inspection(tmp_path, monkeypatch):
    upstream = tmp_path / "codex"
    upstream.touch()
    python = tmp_path / "python"
    python.touch()
    plan = {
        "pane_identifier": "wT:p6G",
        "thread_identifier": "fixture-thread",
        "upstream_binary": str(upstream),
    }
    package = {
        "python": str(python),
        "launch_script": str(tmp_path / "launch_private_session.py"),
    }
    information = {
        "pane_id": plan["pane_identifier"],
        "shell_pid": 70,
        "foreground_process_group_id": 30,
        "foreground_processes": [
            {
                "pid": 30,
                "argv": [
                    package["python"],
                    package["launch_script"],
                    *resume_arguments(plan),
                ],
            },
            {
                "pid": 32,
                "argv": [
                    str(upstream),
                    "--remote",
                    "ws://127.0.0.1/fixture",
                    *resume_arguments(plan)[4:],
                ],
            },
        ],
    }
    pane = {
        "pane_id": plan["pane_identifier"],
        "agent_session": {"agent": "codex", "value": plan["thread_identifier"]},
    }
    sessions = {30: 70, 31: 70, 32: 70, 70: 70}
    groups = {30: 30, 31: 31, 32: 30}
    descriptors = {
        f"/proc/32/fd/{descriptor}": "/dev/pts/999" for descriptor in (0, 1, 2)
    }
    descriptors["/proc/31/fd/2"] = "pipe:[900]"
    for identifier, parent in ((30, 70), (31, 30), (32, 30)):
        directory = tmp_path / "proc" / str(identifier)
        directory.mkdir(parents=True)
        fields = ["S", str(parent), *["0"] * 17, str(identifier * 10)]
        (directory / "stat").write_text(
            f"{identifier} (fixture process) " + " ".join(fields)
        )
        (directory / "exe").symlink_to(python if identifier == 30 else upstream)
    children = tmp_path / "proc/30/task/30/children"
    children.parent.mkdir(parents=True)
    children.write_text("31 32")
    monkeypatch.setattr(
        processes,
        "Path",
        lambda path: tmp_path / str(path).lstrip("/")
        if str(path).startswith("/proc/")
        else Path(path),
    )
    monkeypatch.setattr(
        processes,
        "os",
        SimpleNamespace(
            getsid=sessions.__getitem__,
            getpgid=groups.__getitem__,
            readlink=descriptors.__getitem__,
        ),
    )
    with tempfile.TemporaryDirectory(
        prefix="codex-session-fixture-", dir="/tmp"
    ) as socket_directory:
        socket_path = Path(socket_directory) / "server.sock"
        with socket.socket(socket.AF_UNIX) as server_socket:
            server_socket.bind(str(socket_path))
            arguments = [
                str(upstream),
                "app-server",
                "--listen",
                "unix://" + str(socket_path),
            ]
            (tmp_path / "proc/31/cmdline").write_bytes(
                "\0".join(arguments).encode() + b"\0"
            )
            client_arguments = information["foreground_processes"][1]["argv"]
            client_arguments[2] = "unix://" + str(socket_path)
            (tmp_path / "proc/32/cmdline").write_bytes(
                "\0".join(client_arguments).encode() + b"\0"
            )
            yield SimpleNamespace(
                plan=plan,
                package=package,
                information=information,
                pane=pane,
                sessions=sessions,
                groups=groups,
                descriptors=descriptors,
                directory=tmp_path,
                socket_directory=Path(socket_directory),
            )


def inspect_runtime(fixture):
    return processes.inspect_new_processes(
        fixture.information, fixture.pane, fixture.package, fixture.plan
    )
