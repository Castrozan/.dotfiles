import importlib.util
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

specification = importlib.util.spec_from_file_location(
    "opencli_processes",
    Path(__file__).resolve().parents[2] / "opencli_processes.py",
)
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)


def test_private_browser_pipe_preserves_data_on_graceful_exit(tmp_path):
    specification = importlib.util.spec_from_file_location(
        "opencli_browser",
        Path(__file__).resolve().parents[2] / "opencli_browser.py",
    )
    browser = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(browser)
    fixture = Path(__file__).with_name("pipe_browser_fixture.py")
    process = None
    try:
        with browser.browser_process(
            [sys.executable, str(fixture), str(tmp_path)],
            dict(os.environ),
            subprocess.DEVNULL,
        ) as process:
            deadline = time.monotonic() + 10
            while (
                not (tmp_path / "browser-ready").exists()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            assert (tmp_path / "browser-ready").exists()
    finally:
        if process is not None:
            module.stop_process(process)
    assert process.returncode == 0
    assert (tmp_path / "persisted").read_text() == "retained"


def test_browser_can_flush_storage_before_descendants_are_stopped(tmp_path):
    fixture = Path(__file__).with_name("shutdown_fixture.py")
    process = subprocess.Popen(
        [sys.executable, str(fixture), "browser", str(tmp_path)],
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not (tmp_path / "browser-ready").exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert (tmp_path / "browser-ready").exists()
        module.stop_process(process)
        assert process.returncode == 0
        assert (tmp_path / "persisted").read_text() == "retained"
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
