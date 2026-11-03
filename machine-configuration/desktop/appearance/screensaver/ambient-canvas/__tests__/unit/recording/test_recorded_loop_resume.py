import json
import pathlib
import subprocess
import threading

import pytest

from recording import recorded_loop_capture_pool as capture_pool
from recording.recorded_loop_capture_plan import build_record_index_url
from recording.recorded_loop_capture_target import RecordedLoopCaptureTarget
from recording.recorded_segment_store import store_recorded_segment
from recorded_loop_upload_server import (
    RecordedLoopUploadServer,
    start_recorded_loop_upload_server,
)
import render_ambient_canvas_loop as render

WEB_DIRECTORY = pathlib.Path(__file__).resolve().parents[3] / "web"
BROWSER_FIXTURE = pathlib.Path(__file__).with_name("recording_resume_browser.js")


@pytest.fixture
def browser_capture(monkeypatch):
    upload_limit = [1]
    encoded_compositions = []
    outcome_lock = threading.Lock()

    def drive_browser(request, worker, *ignored):
        target = request.capture_target
        server = start_recorded_loop_upload_server(
            target.loop_directory, str(WEB_DIRECTORY), target.scene_video_directory
        )
        try:
            record_url = build_record_index_url(
                f"http://127.0.0.1:{server.upload_port}/index.html",
                f"http://127.0.0.1:{server.upload_port}/upload",
                target.capture_pixel_dimensions,
                request.configuration,
                worker,
            )
            completed = subprocess.run(
                [
                    "node",
                    str(BROWSER_FIXTURE),
                    str(WEB_DIRECTORY),
                    record_url,
                    str(upload_limit[0]),
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            assert completed.returncode in (0, 77), completed.stderr
            with outcome_lock:
                encoded_compositions.extend(json.loads(completed.stdout))
            return server.received_manifest_bytes
        finally:
            server.shutdown()
            server.server_close()

    monkeypatch.setattr(capture_pool, "drive_record_browser", drive_browser)
    monkeypatch.setattr(capture_pool, "resolve_recording_worker_count", lambda: 2)
    monkeypatch.setattr(
        render, "resolve_chromium_browser_application", lambda: "browser"
    )
    monkeypatch.setattr(
        render, "download_missing_scene_videos", lambda *arguments: None
    )
    return upload_limit, encoded_compositions


def render_pass(target, source="current"):
    return render.render_recorded_loop(
        str(WEB_DIRECTORY / "index.html"), target, source, 1, 1, "#041c38"
    )


def test_interrupted_parallel_pass_resumes_only_missing_segments(
    tmp_path, browser_capture, monkeypatch
):
    upload_limit, encoded_compositions = browser_capture
    target = RecordedLoopCaptureTarget(
        loop_directory=str(tmp_path),
        scene_video_directory=str(tmp_path / "videos"),
        playback_dwell_override_path=str(tmp_path / "dwell"),
        screen_dimensions=(1920, 1080),
        capture_pixel_dimensions=(1920, 1080),
        capture_signature="1920x1080",
    )
    store_recorded_segment(str(tmp_path), "stale-source", "mp4", b"old")
    (tmp_path / "loop.segments.json").write_text(
        '{"segments":[{"file":"segments/stale-source.mp4"}]}'
    )
    (tmp_path / "loop.source").write_text("old")
    old_manifest = (tmp_path / "loop.segments.json").read_bytes()
    assert render_pass(target) is None
    assert sorted(encoded_compositions) == [0, 1]
    assert (tmp_path / "loop.segments.json").read_bytes() == old_manifest
    assert (tmp_path / "loop.source").read_text() == "old"
    kept_segments = {
        path: path.stat().st_mtime_ns
        for path in (tmp_path / "segments").glob("*.mp4")
        if path.stem != "stale-source"
    }
    assert len(kept_segments) == 2
    upload_limit[0] = 0
    encoded_compositions.clear()
    assert render_pass(target)
    assert sorted(encoded_compositions) == [0, 1, 2, 2, 3, 3]
    assert all(
        path.stat().st_mtime_ns == modified for path, modified in kept_segments.items()
    )
    manifest = json.loads((tmp_path / "loop.segments.json").read_text())
    assert len(manifest["segments"]) == 8
    assert not (tmp_path / "segments/stale-source.mp4").exists()
    assert (tmp_path / "loop.source").read_text().strip() == "current"
    committed_manifest = (tmp_path / "loop.segments.json").read_bytes()
    encoded_compositions.clear()
    monkeypatch.setattr(capture_pool, "resolve_recording_worker_count", lambda: 1)
    assert render_pass(target)
    assert encoded_compositions == []
    assert (tmp_path / "loop.segments.json").read_bytes() == committed_manifest


@pytest.mark.parametrize("changed_input", ["size", "source"])
def test_changed_capture_inputs_never_reuse_old_segments(
    tmp_path, browser_capture, monkeypatch, changed_input
):
    upload_limit, encoded_compositions = browser_capture
    upload_limit[0] = 0
    target = RecordedLoopCaptureTarget(
        loop_directory=str(tmp_path),
        scene_video_directory=str(tmp_path / "videos"),
        playback_dwell_override_path=str(tmp_path / "dwell"),
        screen_dimensions=(1920, 1080),
        capture_pixel_dimensions=(1920, 1080),
        capture_signature="1920x1080",
    )
    assert render_pass(target)
    old_files = set((tmp_path / "segments").glob("*.mp4"))
    encoded_compositions.clear()
    if changed_input == "size":
        target = target._replace(capture_pixel_dimensions=(1662, 1080))
    else:
        resolve_inputs = RecordedLoopUploadServer.resolve_fingerprint_inputs
        monkeypatch.setattr(
            RecordedLoopUploadServer,
            "resolve_fingerprint_inputs",
            lambda server: {**resolve_inputs(server), "pipeline": "changed-source"},
        )
    assert render_pass(target, "changed")
    assert len(encoded_compositions) == 8
    assert not old_files.intersection((tmp_path / "segments").glob("*.mp4"))
