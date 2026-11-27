import threading
import time
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import ambient_canvas_browser
from recording import recorded_loop_browser_capture as browser_capture
from recording import recorded_loop_capture_plan as capture_plan
from recording.recorded_loop_capture_plan import RecordingWorker, RecordingConfiguration


@pytest.fixture
def capture_dependencies(monkeypatch, tmp_path):
    profile_directory = tmp_path / "profile"
    profile_directory.mkdir()
    server = Mock(
        upload_port=5000,
        manifest_received_event=threading.Event(),
        received_manifest_bytes=None,
    )
    target = SimpleNamespace(
        loop_directory=str(tmp_path),
        scene_video_directory=str(tmp_path / "videos"),
        screen_dimensions=(1920, 1080),
        capture_pixel_dimensions=(1920, 1080),
    )
    monkeypatch.setattr(
        browser_capture, "start_recorded_loop_upload_server", lambda *arguments: server
    )
    monkeypatch.setattr(
        browser_capture.tempfile, "mkdtemp", lambda **arguments: str(profile_directory)
    )
    monkeypatch.setattr(
        browser_capture,
        "resolve_browser_executable_path",
        lambda application: application,
    )
    monkeypatch.setattr(
        browser_capture,
        "resolve_centered_window_geometry",
        lambda *arguments: (1920, 1080, 0, 0),
    )
    launch = Mock(return_value=Mock())
    launch.return_value.poll.return_value = None
    terminate = Mock()
    monkeypatch.setattr(browser_capture.subprocess, "Popen", launch)
    monkeypatch.setattr(browser_capture, "terminate_browser_process", terminate)
    return server, target, launch, terminate, profile_directory


def run_browser(target, cancellation_event, deadline):
    return browser_capture.drive_record_browser(
        browser_capture.BrowserCaptureRequest(
            "/web/index.html",
            target,
            "browser",
            RecordingConfiguration(None, 60, "#041c38"),
        ),
        RecordingWorker(1, 4),
        deadline,
        cancellation_event,
    )


def test_watchdog_cleans_up_without_deleting_progress(capture_dependencies, tmp_path):
    server, target, launch, terminate, profile_directory = capture_dependencies
    segment_path = tmp_path / "kept.mp4"
    segment_path.write_bytes(b"completed segment")
    started = time.monotonic()
    assert run_browser(target, threading.Event(), started + 0.02) is None
    assert time.monotonic() - started < 1
    terminate.assert_called_once_with(launch.return_value, str(profile_directory))
    server.shutdown.assert_called_once()
    server.server_close.assert_called_once()
    assert not profile_directory.exists()
    assert segment_path.read_bytes() == b"completed segment"
    record_url = next(
        argument
        for argument in launch.call_args.args[0]
        if argument.startswith("--app=")
    )
    assert "workerIndex=1" in record_url
    assert "workerCount=4" in record_url


def test_a_browser_that_dies_before_uploading_fails_the_worker_at_once(
    capture_dependencies,
):
    server, target, launch, terminate, profile_directory = capture_dependencies
    launch.return_value.poll.return_value = -9
    started = time.monotonic()
    with pytest.raises(browser_capture.RecordingBrowserExitedError):
        run_browser(target, threading.Event(), started + 60)
    assert time.monotonic() - started < 3
    terminate.assert_called_once_with(launch.return_value, str(profile_directory))
    assert not profile_directory.exists()


def test_a_browser_that_exits_right_after_uploading_keeps_its_manifest(
    capture_dependencies,
):
    server, target, launch, terminate, profile_directory = capture_dependencies
    server.received_manifest_bytes = b"manifest"

    def exit_after_upload():
        server.manifest_received_event.set()
        return 0

    launch.return_value.poll.side_effect = exit_after_upload
    assert run_browser(target, threading.Event(), time.monotonic() + 60) == b"manifest"


@pytest.mark.parametrize(
    ("platform", "session_bus_address"),
    [("linux", "disabled:"), ("darwin", "unix:path=/run/user/1000/bus")],
)
def test_record_browser_cannot_leave_the_launcher_cgroup_on_linux(
    monkeypatch, capture_dependencies, platform, session_bus_address
):
    server, target, launch, terminate, profile_directory = capture_dependencies
    monkeypatch.setattr(ambient_canvas_browser, "resolve_platform", lambda: platform)
    monkeypatch.setattr(
        capture_plan.os,
        "environ",
        {"DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus", "HOME": "/home"},
    )
    run_browser(target, threading.Event(), time.monotonic() + 0.02)
    assert launch.call_args.kwargs["env"] == {
        "DBUS_SESSION_BUS_ADDRESS": session_bus_address,
        "HOME": "/home",
    }


@pytest.mark.parametrize("termination_failure", [None, "timeout", "missing"])
def test_termination_cleans_only_its_profile_processes(
    monkeypatch, termination_failure, tmp_path
):
    process = Mock()
    if termination_failure == "timeout":
        process.wait.side_effect = subprocess.TimeoutExpired("browser", 5)
    elif termination_failure == "missing":
        process.terminate.side_effect = OSError("already exited")
        process.kill.side_effect = OSError("already exited")
    terminate_children = Mock()
    monkeypatch.setattr(browser_capture.subprocess, "run", terminate_children)
    monkeypatch.setattr(browser_capture.shutil, "which", lambda name: "/usr/bin/pkill")
    profile_directory = str(tmp_path / "ambient-canvas-record-owned")
    browser_capture.terminate_browser_process(process, profile_directory)
    terminate_children.assert_called_once_with(
        ["/usr/bin/pkill", "-f", profile_directory],
        check=False,
        capture_output=True,
    )
    assert process.kill.call_count == int(termination_failure is not None)
