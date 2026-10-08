import importlib.util
import json
import pathlib
import subprocess

import pytest

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "select-herdr-client.py"
)


def _load_module():
    module_spec = importlib.util.spec_from_file_location(
        "select_herdr_client", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


select_herdr_client = _load_module()


def _result(returncode=0, payload=None, stdout=None):
    rendered_stdout = stdout
    if rendered_stdout is None:
        rendered_stdout = "" if payload is None else json.dumps(payload)
    return subprocess.CompletedProcess([], returncode, rendered_stdout, "")


def _executable(tmp_path, package_name):
    executable = tmp_path / package_name / "bin" / "herdr"
    executable.parent.mkdir(parents=True)
    executable.write_text("")
    executable.chmod(0o755)
    return executable


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["--session", "work"],
        ["completion", "zsh"],
        ["config", "reset-keys"],
        ["integration", "install", "codex"],
        ["status", "server"],
        ["api", "schema"],
        ["server"],
        ["server", "live-handoff"],
    ],
)
def test_local_and_tui_commands_use_the_installed_client(arguments):
    assert not select_herdr_client.command_requires_running_server_client(arguments)


@pytest.mark.parametrize(
    "arguments",
    [
        ["agent", "exit"],
        ["workspace", "list"],
        ["api", "snapshot"],
        ["server", "stop"],
    ],
)
def test_socket_commands_use_the_running_server_client(arguments):
    assert select_herdr_client.command_requires_running_server_client(arguments)


def test_running_server_client_is_selected_by_socket_owner(tmp_path, monkeypatch):
    installed_executable = _executable(tmp_path, "installed")
    running_executable = _executable(tmp_path, "running")
    socket_path = tmp_path / "herdr.sock"

    def run_command(*arguments):
        if arguments[0] == str(installed_executable):
            return _result(payload={"running": True, "socket": str(socket_path)})
        if "-t" in arguments:
            return _result(stdout="4242\n")
        return _result(
            stdout=(
                f"p4242\nn{running_executable}\nn/nix/store/library/lib/example.dylib\n"
            )
        )

    monkeypatch.setattr(select_herdr_client, "run_command", run_command)

    selected = select_herdr_client.select_client_executable(
        str(installed_executable), ["agent", "exit"]
    )

    assert selected == running_executable


def test_socket_owner_lookup_excludes_unrelated_process_files(tmp_path, monkeypatch):
    socket_path = tmp_path / "herdr.sock"

    def run_command(*arguments):
        assert "-a" in arguments, "socket and command selections must intersect"
        assert "-c" in arguments, "socket discovery must scope process file queries"
        assert arguments[arguments.index("-c") + 1] == "herdr"
        return _result(stdout="4242\n")

    monkeypatch.setattr(select_herdr_client, "run_command", run_command)

    assert select_herdr_client.read_socket_owner_process_id(socket_path) == 4242


def test_installed_client_is_selected_when_no_server_is_running(tmp_path, monkeypatch):
    installed_executable = _executable(tmp_path, "installed")
    monkeypatch.setattr(
        select_herdr_client,
        "run_command",
        lambda *arguments: _result(payload={"running": False}),
    )

    selected = select_herdr_client.select_client_executable(
        str(installed_executable), ["agent", "list"]
    )

    assert selected == installed_executable


def test_unknown_socket_owner_fails_instead_of_using_a_mismatched_client(
    tmp_path, monkeypatch
):
    installed_executable = _executable(tmp_path, "installed")
    socket_path = tmp_path / "herdr.sock"
    results = iter(
        [
            _result(payload={"running": True, "socket": str(socket_path)}),
            _result(returncode=1),
        ]
    )
    monkeypatch.setattr(
        select_herdr_client, "run_command", lambda *arguments: next(results)
    )

    with pytest.raises(
        select_herdr_client.ServerClientSelectionError,
        match="cannot identify the process serving",
    ):
        select_herdr_client.select_client_executable(
            str(installed_executable), ["agent", "exit"]
        )


def test_running_server_package_is_retained_as_an_indirect_gc_root(
    tmp_path, monkeypatch
):
    running_executable = _executable(tmp_path, "running")
    root_path = tmp_path / "state" / "running-server-package"
    commands = []
    monkeypatch.setattr(
        select_herdr_client,
        "run_command",
        lambda *arguments: commands.append(arguments) or _result(),
    )

    select_herdr_client.retain_executable_package(running_executable, root_path)

    assert commands == [
        (
            "nix-store",
            "--realise",
            str(running_executable.parents[1]),
            "--add-root",
            str(root_path),
            "--indirect",
        )
    ]


def test_non_package_executable_cannot_be_retained(tmp_path):
    executable = tmp_path / "herdr"
    executable.write_text("")

    with pytest.raises(
        select_herdr_client.ServerClientSelectionError,
        match="cannot identify Herdr package",
    ):
        select_herdr_client.retain_executable_package(
            executable, tmp_path / "retention-root"
        )
