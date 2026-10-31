import importlib.util
import signal
from pathlib import Path
from unittest.mock import Mock

import pytest

HYPRLAND_WINDOW_RULES = (
    Path(__file__).resolve().parents[9]
    / "machine-configuration/desktop/desktop-environments/hyprland"
    / "program-configuration/conf.d/windows.conf"
)


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
    monkeypatch.setattr(
        module.os,
        "kill",
        Mock(side_effect=lambda *_: (process / "cmdline").unlink(missing_ok=True)),
    )
    return module, profile, process


def test_output_browser_advertises_the_class_the_compositor_hides(runtime, monkeypatch):
    module, profile, process = runtime
    launched_arguments = []

    def launch(arguments, **_):
        launched_arguments.extend(arguments)
        (profile / "DevToolsActivePort").write_text("9222\n/devtools/browser")
        return Mock(pid=123, poll=Mock(return_value=None))

    monkeypatch.setattr(module.subprocess, "Popen", launch)
    module.start("http://localhost:3000/?output=1")

    window_rules = HYPRLAND_WINDOW_RULES.read_text()
    assert f"--class={module.BROWSER_WINDOW_CLASS}" in launched_arguments
    assert f"match:class ^({module.BROWSER_WINDOW_CLASS})$" in window_rules


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


def test_stale_browser_locks_are_removed_without_deleting_profile(runtime):
    module, profile, process = runtime
    (profile / "SingletonLock").symlink_to(f"{module.socket.gethostname()}-456")
    (profile / "SingletonCookie").symlink_to("cookie")
    (profile / "preferences").write_text("preserved")
    module.remove_stale_locks(profile)
    assert not (profile / "SingletonLock").is_symlink()
    assert (profile / "preferences").read_text() == "preserved"


def test_existing_process_prevents_lock_removal(runtime):
    module, profile, process = runtime
    (process / "cmdline").write_bytes(b"another-process")
    (profile / "SingletonLock").symlink_to(f"{module.socket.gethostname()}-123")
    module.remove_stale_locks(profile)
    assert (profile / "SingletonLock").is_symlink()


def test_zombie_browser_lock_does_not_block_restart(runtime):
    module, profile, process = runtime
    (process / "cmdline").write_bytes(b"")
    (profile / "SingletonLock").symlink_to(f"{module.socket.gethostname()}-123")
    module.remove_stale_locks(profile)
    assert not (profile / "SingletonLock").is_symlink()


def test_singleton_pid_tracks_the_browser_after_launcher_exits(runtime):
    module, profile, process = runtime
    browser = process.parent / "456"
    browser.mkdir()
    (browser / "cmdline").write_bytes(f"chromium\0--user-data-dir={profile}\0".encode())
    (profile / "SingletonLock").symlink_to(f"{module.socket.gethostname()}-456")
    assert module.owned_process(profile) == 456


def test_chromium_process_title_preserves_exact_profile_ownership(runtime):
    module, profile, process = runtime
    (process / "cmdline").write_bytes(
        f"chromium --user-data-dir={profile} --app=http://localhost:3000/\0".encode()
    )
    assert module.owned_process(profile) == 123
    (process / "cmdline").write_bytes(
        f"chromium --user-data-dir={profile}-another --app=http://localhost:3000/\0".encode()
    )
    assert module.owned_process(profile) is None
