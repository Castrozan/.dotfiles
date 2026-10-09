import json
import os
from pathlib import Path
import sys
import time

import pytest

import launch_private_session as launcher


@pytest.fixture
def running_codex_stub(tmp_path, monkeypatch):
    binary = tmp_path / "codex"
    binary.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "import os\n"
        "from pathlib import Path\n"
        "import signal\n"
        "import subprocess\n"
        "import sys\n"
        "import time\n"
        "state = Path(os.environ['CODEX_TEST_STATE_DIRECTORY'])\n"
        "if 'app-server' in sys.argv:\n"
        "    os.write(2, b'backend error\\n')\n"
        "    if os.environ.get('CODEX_TEST_STARTUP_FAILURE'):\n"
        "        os.write(2, b'older output' * 8192)\n"
        "        os.write(2, b'\\nlast startup error\\x1b\\r\\n')\n"
        "        sys.exit(23)\n"
        "    if os.environ.get('CODEX_TEST_CHILD_PROCESS'):\n"
        "        child = subprocess.Popen([sys.executable, '-c',\n"
        "            'import signal; signal.pause()'])\n"
        "        (state / 'child.json').write_text(json.dumps(child.pid))\n"
        "        def stop_group(signal_number, frame):\n"
        "            child.wait(timeout=1.0)\n"
        "            sys.exit(0)\n"
        "        signal.signal(signal.SIGTERM, stop_group)\n"
        "    descriptor = os.fstat(2)\n"
        "    (state / 'server.json').write_text(json.dumps({\n"
        "        'process_identifier': os.getpid(),\n"
        "        'stderr_device': descriptor.st_dev,\n"
        "        'stderr_inode': descriptor.st_ino,\n"
        "        'directory': os.environ['CODEX_SESSION_SOCKET_PATH'],\n"
        "    }))\n"
        "    if os.environ.get('CODEX_TEST_RUNTIME_FAILURE'):\n"
        "        while not (state / 'client.ready').exists():\n"
        "            time.sleep(0.01)\n"
        "        os.write(2, b'backend failed with active client\\n')\n"
        "        sys.exit(29)\n"
        "    while True:\n"
        "        signal.pause()\n"
        "os.write(2, b'terminal client\\n')\n"
        "(state / 'client.ready').touch()\n"
        "time.sleep(5 if os.environ.get('CODEX_TEST_RUNTIME_FAILURE') else 0.05)\n"
        "sys.exit(7)\n"
    )
    binary.chmod(0o755)
    monkeypatch.setenv("CODEX_LAUNCHER_BINARY", str(binary))
    monkeypatch.setenv("CODEX_TEST_STATE_DIRECTORY", str(tmp_path))

    def wait_for_stub(server, socket_path):
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if (tmp_path / "server.json").exists():
                return
            if server.poll() is not None:
                raise RuntimeError("stub server exited during startup")
            time.sleep(0.01)
        raise TimeoutError("stub server did not become ready")

    monkeypatch.setattr(launcher, "wait_for_session_server", wait_for_stub)
    return tmp_path


def test_backend_stderr_is_isolated_from_terminal_client(running_codex_stub, capfd):
    terminal_descriptor = os.fstat(2)
    assert launcher.run_private_session([]) == 7
    server_state = json.loads((running_codex_stub / "server.json").read_text())
    assert capfd.readouterr().err == "terminal client\n"
    assert (
        server_state["stderr_device"],
        server_state["stderr_inode"],
    ) != (terminal_descriptor.st_dev, terminal_descriptor.st_ino)
    with pytest.raises(ProcessLookupError):
        os.kill(server_state["process_identifier"], 0)
    assert not Path(server_state["directory"]).parent.exists()


def test_startup_failure_returns_bounded_backend_details_after_server_teardown(
    running_codex_stub, monkeypatch, capfd
):
    monkeypatch.setenv("CODEX_TEST_STARTUP_FAILURE", "1")
    monkeypatch.setattr(sys, "argv", ["codex"])
    assert launcher.main() == 1
    failure = capfd.readouterr().err
    assert failure.startswith("stub server exited during startup\n")
    assert failure.endswith("last startup error\n")
    assert len(failure.encode("utf-8")) < 4200
    assert "\x1b" not in failure
    assert "terminal client" not in failure


def test_client_exit_reaps_backend_process_group_with_descendant(
    running_codex_stub, monkeypatch, capfd
):
    monkeypatch.setenv("CODEX_TEST_CHILD_PROCESS", "1")
    assert launcher.run_private_session([]) == 7
    server_state = json.loads((running_codex_stub / "server.json").read_text())
    child_identifier = json.loads((running_codex_stub / "child.json").read_text())
    with pytest.raises(ProcessLookupError):
        os.killpg(server_state["process_identifier"], 0)
    with pytest.raises(ProcessLookupError):
        os.kill(child_identifier, 0)
    assert capfd.readouterr().err == "terminal client\n"


def test_backend_failure_terminates_client_without_writing_diagnostics_to_terminal(
    running_codex_stub, monkeypatch, capfd
):
    monkeypatch.setenv("CODEX_TEST_RUNTIME_FAILURE", "1")
    assert launcher.run_private_session([]) == 143
    server_state = json.loads((running_codex_stub / "server.json").read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(server_state["process_identifier"], 0)
    assert capfd.readouterr().err == "terminal client\n"
