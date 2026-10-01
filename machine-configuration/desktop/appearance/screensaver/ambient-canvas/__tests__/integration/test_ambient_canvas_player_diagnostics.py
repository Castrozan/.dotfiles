import json
import os
import pathlib
import signal
import subprocess
import sys

import pytest


SUPERVISOR_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts/ambient_canvas_media/playback/supervise_ambient_canvas_player.py"
)


@pytest.mark.parametrize("exit_code", [0, 17])
def test_player_output_and_exit_status_survive_the_player(tmp_path, exit_code):
    completed = subprocess.run(
        [
            sys.executable,
            str(SUPERVISOR_PATH),
            str(tmp_path),
            sys.executable,
            "-c",
            f"import sys; print('player output'); print('player error', file=sys.stderr); sys.exit({exit_code})",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["status"] == ("exited" if exit_code == 0 else "failed")
    assert report["exit_code"] == exit_code
    assert report["signal"] is None
    assert report["player_pid"] > 0
    assert report["duration_seconds"] >= 0
    assert report["started_at"] <= report["finished_at"]
    assert "player error" in report["output_tail"]
    log = (tmp_path / "player.log").read_text()
    assert "player output" in log
    assert "player error" in log
    assert "player_started" in log
    assert "player_exited" in log


def test_an_uncatchable_player_signal_is_reported_by_the_supervisor(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            str(SUPERVISOR_PATH),
            str(tmp_path),
            sys.executable,
            "-c",
            "import os, signal; print('before kill', flush=True); os.kill(os.getpid(), signal.SIGKILL)",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["status"] == "failed"
    assert report["exit_code"] == -signal.SIGKILL
    assert report["signal"] == "SIGKILL"
    assert "before kill" in report["output_tail"]


def test_a_player_that_cannot_start_leaves_a_report(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SUPERVISOR_PATH), str(tmp_path), "/missing/player"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 1
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["status"] == "launch_failed"
    assert "No such file" in report["error"]


def test_noisy_player_logs_and_report_tail_have_bounded_size(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            str(SUPERVISOR_PATH),
            str(tmp_path),
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('x' * (5 * 1024 * 1024)); sys.stdout.write('last output'); sys.exit(3)",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    log_paths = list(tmp_path.glob("player.log*"))
    assert len(log_paths) <= 3
    assert all(path.stat().st_size <= 1024 * 1024 for path in log_paths)
    report = json.loads((tmp_path / "report.json").read_text())
    assert len(report["output_tail"]) <= 64 * 1024
    assert report["output_tail"].endswith("last output")


def test_inherited_output_pipe_does_not_hide_the_player_exit(tmp_path):
    supervisor = subprocess.Popen(
        [
            sys.executable,
            str(SUPERVISOR_PATH),
            str(tmp_path),
            sys.executable,
            "-c",
            "import os, subprocess, sys; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); os._exit(19)",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        supervisor.wait(timeout=5)
        report = json.loads((tmp_path / "report.json").read_text())
        assert report["exit_code"] == 19
        assert (
            "player_output_still_open_after_exit"
            in (tmp_path / "player.log").read_text()
        )
    finally:
        os.killpg(supervisor.pid, signal.SIGTERM)
        supervisor.communicate(timeout=5)
