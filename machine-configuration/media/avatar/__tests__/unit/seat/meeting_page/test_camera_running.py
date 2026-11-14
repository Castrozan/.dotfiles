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
