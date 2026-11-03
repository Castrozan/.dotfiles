import threading
import time
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from recording import recorded_loop_browser_capture as browser_capture
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


def test_cancelled_pass_stops_its_browser(capture_dependencies):
    server, target, launch, terminate, profile_directory = capture_dependencies
    cancellation_event = threading.Event()
    cancellation_event.set()
    assert run_browser(target, cancellation_event, time.monotonic() + 1800) is None
    terminate.assert_called_once()


def test_browser_launch_failure_closes_upload_server(capture_dependencies):
    server, target, launch, terminate, profile_directory = capture_dependencies
    launch.side_effect = OSError("cannot launch")
    with pytest.raises(OSError, match="cannot launch"):
        run_browser(target, threading.Event(), time.monotonic() + 1800)
    server.shutdown.assert_called_once()
    server.server_close.assert_called_once()
    assert not profile_directory.exists()
    terminate.assert_not_called()


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
