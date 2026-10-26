import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_devtools_connect as connection
from chrome_devtools_request import finish_process


@pytest.fixture
def fixture_commands(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("CODEX_THREAD_ID", "connection-test")
    for variable in (
        "HERDR_ENV",
        "HERDR_SESSION",
        "HERDR_SOCKET_PATH",
        "HERDR_PANE_ID",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("BROWSER_EVENT_LOG", str(tmp_path / "events"))
    upstream = tmp_path / "upstream"
    upstream.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys, time\n"
        "from pathlib import Path\n"
        "operation = sys.argv[3]\n"
        "with open(os.environ['BROWSER_EVENT_LOG'], 'a') as stream: stream.write(operation + '\\n')\n"
        "if operation == 'list_pages':\n"
        "    Path(os.environ['BROWSER_EVENT_LOG'] + '.request.pid').write_text(str(os.getpid()))\n"
        "    if os.environ.get('BROWSER_BLOCK'): time.sleep(20)\n"
        "    print(json.dumps({'pages': [{'id': 1, 'url': 'about:blank'}]}))\n"
    )
    upstream.chmod(0o700)
    helper = tmp_path / "helper.py"
    helper.write_text(
        "import os, sys, time\n"
        "from pathlib import Path\n"
        "Path(os.environ['BROWSER_EVENT_LOG'] + '.helper.pid').write_text(str(os.getpid()))\n"
        "with open(os.environ['BROWSER_EVENT_LOG'], 'a') as stream: stream.write('helper.ready\\n')\n"
        "print('ready', flush=True)\n"
        "if os.environ.get('HELPER_REJECT'): sys.exit(7)\n"
        "time.sleep(20)\n"
    )
    configuration = {
        "upstreamExecutable": str(upstream),
        "homeDirectory": str(tmp_path),
        "ffmpegExecutable": "/ffmpeg",
        "chromeExecutable": "/chrome",
        "consentHelper": [sys.executable, str(helper)],
    }
    path = tmp_path / "configuration.json"
    path.write_text(json.dumps(configuration))
    command_path = Path(connection.__file__).with_name("chrome_devtools_command.py")
    return [sys.executable, str(command_path), str(path)], tmp_path / "events"


def test_helper_is_ready_before_connection_and_all_children_finish(fixture_commands):
    command, events = fixture_commands
    result = subprocess.run(
        [*command, "connect", "--approve-once", "token"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert events.read_text().splitlines() == ["helper.ready", "start", "list_pages"]
    for suffix in (".request.pid", ".helper.pid"):
        with pytest.raises(ProcessLookupError):
            os.kill(int(Path(str(events) + suffix).read_text()), 0)


def test_blocked_connection_leaves_tools_available_and_rejects_parallel_grants(
    fixture_commands, monkeypatch
):
    command, events = fixture_commands
    monkeypatch.setenv("BROWSER_BLOCK", "1")
    process = subprocess.Popen(
        [*command, "connect", "--manual-once", "--timeout", "3"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    started = time.monotonic()
    try:
        deadline = started + 2
        while not events.exists() or "list_pages" not in events.read_text():
            assert time.monotonic() < deadline
            time.sleep(0.02)
        status = subprocess.run([*command, "status"], capture_output=True, timeout=1)
        assert status.returncode == 0
        environment = {**os.environ, "CODEX_THREAD_ID": "competing-task"}
        second = subprocess.run(
            [*command, "connect"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=1,
        )
        assert second.returncode == 1
        assert "Attached Chrome is busy" in second.stderr
        _, error = process.communicate(timeout=5)
        assert process.returncode == 1
        assert "deadline expired" in error
        assert time.monotonic() - started < 5
        assert events.read_text().splitlines() == [
            "start",
            "list_pages",
            "status",
            "stop",
        ]
    finally:
        finish_process(process)


def test_rejected_helper_cancels_request_and_cleans_owned_worker(
    fixture_commands, monkeypatch
):
    command, events = fixture_commands
    monkeypatch.setenv("BROWSER_BLOCK", "1")
    monkeypatch.setenv("HELPER_REJECT", "1")
    result = subprocess.run(
        [*command, "connect", "--approve-once", "token"],
        capture_output=True,
        text=True,
        timeout=4,
    )
    assert result.returncode == 1
    assert "rejected this attempt" in result.stderr
    assert events.read_text().splitlines()[-1] == "stop"


def test_cancellation_stops_the_request_and_temporary_helper(
    fixture_commands, monkeypatch
):
    command, events = fixture_commands
    monkeypatch.setenv("BROWSER_BLOCK", "1")
    process = subprocess.Popen(
        [*command, "connect", "--approve-once", "token"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 2
        while not events.exists() or "list_pages" not in events.read_text():
            assert time.monotonic() < deadline
            time.sleep(0.02)
        process.terminate()
        _, error = process.communicate(timeout=4)
        assert process.returncode == 1
        assert "cancelled" in error
        assert events.read_text().splitlines()[-1] == "stop"
        for suffix in (".request.pid", ".helper.pid"):
            with pytest.raises(ProcessLookupError):
                os.kill(int(Path(str(events) + suffix).read_text()), 0)
    finally:
        finish_process(process)
