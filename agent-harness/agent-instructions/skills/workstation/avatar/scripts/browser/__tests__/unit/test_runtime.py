import importlib.util
import signal
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    specification = importlib.util.spec_from_file_location(
        "avatar_browser_runtime", Path(__file__).resolve().parents[2] / "runtime.py"
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "browser.pid").write_text("123")
    process = tmp_path / "proc/123"
    process.mkdir(parents=True)
    monkeypatch.setattr(module, "profile_directory", lambda: profile)
    monkeypatch.setattr(
        module,
        "Path",
        lambda value: tmp_path / "proc" if value == "/proc" else Path(value),
    )
    monkeypatch.setattr(module.os, "kill", Mock())
    return module, profile, process


def test_stop_closes_only_the_owned_avatar_browser(runtime):
    module, profile, process = runtime
    (process / "cmdline").write_bytes(f"chromium\0--user-data-dir={profile}\0".encode())
    (profile / "session").write_text("preserved")
    module.stop()
    module.os.kill.assert_called_once_with(123, signal.SIGTERM)
    assert (profile / "session").read_text() == "preserved"


def test_reused_pid_cannot_close_another_browser(runtime):
    module, profile, process = runtime
    (process / "cmdline").write_bytes(b"chromium\0--user-data-dir=/shared/browser\0")
    module.stop()
    module.os.kill.assert_not_called()


def test_exited_browser_is_already_stopped(runtime):
    module, profile, process = runtime
    module.stop()
    module.os.kill.assert_not_called()
