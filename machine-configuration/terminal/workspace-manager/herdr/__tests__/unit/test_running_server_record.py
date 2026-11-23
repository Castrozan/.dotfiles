import importlib.util
import json
import pathlib
import subprocess

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


def test_selected_running_server_is_recorded_with_its_socket_and_process(
    tmp_path, monkeypatch
):
    installed_executable = _executable(tmp_path, "installed")
    running_executable = _executable(tmp_path, "running")
    socket_path = tmp_path / "herdr.sock"
    record_path = tmp_path / "state" / "herdr" / "running-server-client"

    def run_command(*arguments):
        if arguments[0] == str(installed_executable):
            return _result(payload={"running": True, "socket": str(socket_path)})
        if "-t" in arguments:
            return _result(stdout="4242\n")
        return _result(stdout=f"p4242\nn{running_executable}\n")

    monkeypatch.setattr(select_herdr_client, "run_command", run_command)

    select_herdr_client.select_client_executable(
        str(installed_executable), ["agent", "exit"], record_path
    )

    assert record_path.read_text() == f"{socket_path}\n4242\n"
    assert list(record_path.parent.iterdir()) == [record_path]


def test_unwritable_record_location_still_selects_the_running_server(
    tmp_path, monkeypatch
):
    installed_executable = _executable(tmp_path, "installed")
    running_executable = _executable(tmp_path, "running")
    socket_path = tmp_path / "herdr.sock"
    occupied_by_a_file = tmp_path / "state"
    occupied_by_a_file.write_text("")

    def run_command(*arguments):
        if arguments[0] == str(installed_executable):
            return _result(payload={"running": True, "socket": str(socket_path)})
        if "-t" in arguments:
            return _result(stdout="4242\n")
        return _result(stdout=f"p4242\nn{running_executable}\n")

    monkeypatch.setattr(select_herdr_client, "run_command", run_command)

    selected = select_herdr_client.select_client_executable(
        str(installed_executable),
        ["agent", "exit"],
        occupied_by_a_file / "herdr" / "running-server-client",
    )

    assert selected == running_executable
