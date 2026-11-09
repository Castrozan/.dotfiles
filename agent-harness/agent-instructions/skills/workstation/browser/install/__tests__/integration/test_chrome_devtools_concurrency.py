import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

from chrome_devtools_request import finish_process
from chrome_devtools_session import ChromeDevtoolsSession


@pytest.fixture
def ready_workers(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    upstream = tmp_path / "upstream"
    upstream.write_text(
        f"#!{sys.executable}\n"
        "import os, sys, time\n"
        "from pathlib import Path\n"
        "if os.environ.get('BROWSER_BLOCK'):\n"
        "    Path(os.environ['BROWSER_READY']).touch()\n"
        "    deadline = time.monotonic() + 5\n"
        "    while not Path(os.environ['BROWSER_RELEASE']).exists():\n"
        "        if time.monotonic() > deadline: sys.exit(8)\n"
        "        time.sleep(0.01)\n"
        "print(sys.argv[2])\n"
    )
    upstream.chmod(0o700)
    configuration = tmp_path / "configuration.json"
    configuration.write_text(
        json.dumps(
            {
                "upstreamExecutable": str(upstream),
                "homeDirectory": str(tmp_path),
                "ffmpegExecutable": "/ffmpeg",
                "chromeExecutable": "/chrome",
            }
        )
    )
    sessions = {}
    for owner in ("first", "second"):
        monkeypatch.setenv("CODEX_THREAD_ID", owner)
        session = ChromeDevtoolsSession.current(tmp_path)
        session.record_mode("attached", str(upstream))
        session.pid_file.parent.mkdir(parents=True)
        session.pid_file.write_text(str(os.getpid()))
        sessions[owner] = session
    command = [
        sys.executable,
        str(
            Path(__file__).resolve().parents[2]
            / "scripts/chrome-devtools/chrome_devtools_command.py"
        ),
        str(configuration),
    ]
    return command, sessions, tmp_path


@pytest.mark.parametrize("same_owner", [False, True])
@pytest.mark.parametrize("operation", ["list_pages", "take_snapshot"])
def test_commands_overlap_only_between_distinct_workers(
    ready_workers, same_owner, operation
):
    command, sessions, directory = ready_workers
    ready = directory / "ready"
    release = directory / "release"
    first = subprocess.Popen(
        [*command, "take_snapshot", "1"],
        env={
            **os.environ,
            "CODEX_THREAD_ID": "first",
            "BROWSER_BLOCK": "1",
            "BROWSER_READY": str(ready),
            "BROWSER_RELEASE": str(release),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 3
        while not ready.exists():
            assert first.poll() is None
            assert time.monotonic() < deadline
            time.sleep(0.01)
        owner = "first" if same_owner else "second"
        second = subprocess.run(
            [*command, operation, *(["1"] if operation == "take_snapshot" else [])],
            env={**os.environ, "CODEX_THREAD_ID": owner},
            capture_output=True,
            text=True,
            timeout=2,
        )
        if same_owner:
            assert second.returncode == 1
            assert "This Chrome DevTools worker is busy" in second.stderr
        else:
            assert second.returncode == 0, second.stderr
            assert second.stdout.strip() == sessions[owner].identifier
        assert first.poll() is None
        release.touch()
        output, error = first.communicate(timeout=2)
        assert first.returncode == 0, error
        assert output.strip() == sessions["first"].identifier
    finally:
        finish_process(first)
        first.stdout.close()
        first.stderr.close()


def test_connection_consent_does_not_block_another_ready_worker(ready_workers):
    command, sessions, _ = ready_workers
    with sessions["first"].connection_locked():
        result = subprocess.run(
            [*command, "list_pages"],
            env={**os.environ, "CODEX_THREAD_ID": "second"},
            capture_output=True,
            text=True,
            timeout=2,
        )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == sessions["second"].identifier
