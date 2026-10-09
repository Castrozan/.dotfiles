from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace

import pytest

from agent_session import codex_migration_processes as processes


@pytest.fixture
def process_inspection(tmp_path, monkeypatch):
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
                    *processes.resume_arguments(plan),
                ],
            },
            {
                "pid": 32,
                "argv": [
                    str(upstream),
                    "--remote",
                    "ws://127.0.0.1/fixture",
                    *processes.resume_arguments(plan)[4:],
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
            (tmp_path / "proc/32/cmdline").write_bytes(str(upstream).encode() + b"\0")
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


def inspect(fixture):
    return processes.inspect_new_processes(
        fixture.information, fixture.pane, fixture.package, fixture.plan
    )


def test_replacement_proves_pane_session_separate_backend_group_and_descriptors(
    process_inspection,
):
    result = inspect(process_inspection)
    assert result["session_id"] == 70
    assert result["process_groups"] == {"launcher": 30, "client": 30, "server": 31}
    assert result["births"]["server"] == {
        "start_ticks": 310,
        "state": "S",
        "parent": 30,
    }
    assert result["server_stderr"] == "pipe:[900]"
    assert result["diagnostic_sizes"] == {
        "server-stderr.log": 0,
        "server-stderr.previous.log": 0,
    }


@pytest.mark.parametrize("identifier", [30, 31, 32])
def test_detached_replacement_session_is_refused(process_inspection, identifier):
    process_inspection.sessions[identifier] = 999
    with pytest.raises(ValueError, match="session"):
        inspect(process_inspection)


@pytest.mark.parametrize("identifier, group", [(30, 999), (31, 30), (32, 32)])
def test_changed_foreground_or_backend_group_is_refused(
    process_inspection, identifier, group
):
    process_inspection.groups[identifier] = group
    with pytest.raises(ValueError, match="group|foreground"):
        inspect(process_inspection)


def test_orphaned_child_is_refused(process_inspection):
    path = process_inspection.directory / "proc/31/stat"
    path.write_text(path.read_text().replace(" S 30 ", " S 1815 "))
    with pytest.raises(ValueError, match="ownership"):
        inspect(process_inspection)


def test_changed_upstream_executable_is_refused(process_inspection):
    path = process_inspection.directory / "proc/31/exe"
    path.unlink()
    path.symlink_to(process_inspection.package["python"])
    with pytest.raises(ValueError, match="executable"):
        inspect(process_inspection)


def test_backend_stderr_must_remain_a_pipe(process_inspection):
    process_inspection.descriptors["/proc/31/fd/2"] = "/dev/pts/999"
    with pytest.raises(ValueError, match="pipe"):
        inspect(process_inspection)


def test_client_descriptors_must_share_the_terminal(process_inspection):
    process_inspection.descriptors["/proc/32/fd/0"] = "pipe:[900]"
    with pytest.raises(ValueError, match="descriptors"):
        inspect(process_inspection)


def test_diagnostic_limit_is_enforced(process_inspection):
    with (process_inspection.socket_directory / "server-stderr.log").open(
        "wb"
    ) as stream:
        stream.truncate(1024 * 1024 + 1)
    with pytest.raises(ValueError, match="1 MiB"):
        inspect(process_inspection)


def test_changed_birth_during_inspection_is_refused(process_inspection, monkeypatch):
    original = processes.process_birth
    inspections = 0

    def changing_birth(identifier):
        nonlocal inspections
        inspections += 1
        birth = original(identifier)
        return {**birth, "start_ticks": 999} if inspections > 3 else birth

    monkeypatch.setattr(processes, "process_birth", changing_birth)
    with pytest.raises(ValueError, match="birth changed"):
        inspect(process_inspection)
