import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "precompute_loop.py"


def run_until_replaying(cache_directory, force=False):
    arguments = [sys.executable, str(SCRIPT), "--seconds", "1"]
    if force:
        arguments.append("--force")
    arguments += ["--", sys.executable, "-u", "-c", "print('loop-frame', flush=True)"]
    process = subprocess.Popen(
        arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "XDG_CACHE_HOME": str(cache_directory)},
        start_new_session=True,
    )
    output = b""
    deadline = time.monotonic() + 15
    try:
        while output.count(b"loop-frame") < 2 and time.monotonic() < deadline:
            ready, _, _ = select.select([process.stdout], [], [], 0.1)
            if ready:
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    break
                output += chunk
        assert output.count(b"loop-frame") >= 2
        process.send_signal(signal.SIGTERM)
        remaining, errors = process.communicate(timeout=5)
        assert process.returncode == 0, errors.decode()
        assert (output + remaining).endswith(b"\x1b[?25h\x1b[0m")
        return errors.decode()
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def test_recording_cache_replay_force_and_signal_restore_terminal(tmp_path):
    assert "recording 1s" in run_until_replaying(tmp_path)
    cast_files = list(tmp_path.rglob("cast.bin"))
    assert len(cast_files) == 1 and cast_files[0].read_bytes().startswith(b"PCL1")
    before = cast_files[0].stat().st_mtime_ns
    assert "recording" not in run_until_replaying(tmp_path)
    assert cast_files[0].stat().st_mtime_ns == before
    assert "recording 1s" in run_until_replaying(tmp_path, force=True)
    assert cast_files[0].stat().st_mtime_ns > before
    assert list(tmp_path.rglob("*.tmp.*")) == []


def test_missing_command_and_empty_capture_fail_with_context(tmp_path):
    environment = {**os.environ, "XDG_CACHE_HOME": str(tmp_path)}
    missing = subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert missing.returncode == 2 and "no command given" in missing.stderr
    silent_command = shutil.which("true")
    assert silent_command is not None
    empty = subprocess.run(
        [sys.executable, str(SCRIPT), "--seconds", "0.1", "--", silent_command],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert empty.returncode == 1 and "nothing captured" in empty.stderr
