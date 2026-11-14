from types import SimpleNamespace
from unittest.mock import Mock

import meeting_camera
import pytest


@pytest.mark.parametrize(("returncode", "expected"), [(0, True), (1, False)])
def test_the_camera_runs_when_a_process_matches_the_collection_flag(
    monkeypatch, returncode, expected
):
    search = Mock(return_value=SimpleNamespace(returncode=returncode))
    monkeypatch.setattr(meeting_camera.subprocess, "run", search)
    assert meeting_camera.running() is expected
    assert search.call_args.args[0] == [
        "/usr/bin/pgrep",
        "-f",
        "--",
        "--collection Avatar",
    ]
    assert search.call_args.kwargs["timeout"]


@pytest.fixture
def report(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(meeting_camera.local_seat, "end_processes_matching", Mock())
    report = tmp_path / ".local/share/avatar/virtual-camera-report"
    report.parent.mkdir(parents=True)
    return report


@pytest.mark.parametrize(
    ("reported", "expected"), [("active", True), ("inactive", False), (None, False)]
)
def test_the_camera_started_once_obs_reported_it_active(report, reported, expected):
    if reported:
        report.write_text(reported)
    assert meeting_camera.started() is expected


def test_a_stopped_camera_no_longer_counts_as_started(report):
    report.write_text("active")
    meeting_camera.stop()
    assert not meeting_camera.started()
