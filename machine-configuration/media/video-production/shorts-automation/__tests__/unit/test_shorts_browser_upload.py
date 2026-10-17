import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from shorts_browser_upload import upload_video


@pytest.fixture
def upload_environment(tmp_path, monkeypatch):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video-fixture")
    run = Mock(
        return_value=SimpleNamespace(
            stdout=json.dumps({"ok": True, "data": {"uploaded": True}})
        )
    )
    monkeypatch.setattr("shorts_browser_upload.subprocess.run", run)
    return video, run


def test_upload_preserves_filename_and_exact_tab(upload_environment):
    video, run = upload_environment
    command = ["opencli", "browser", "--session", "current-run"]
    assert upload_video(
        [str(video), "--tab", "own-tab", "--selector", "#upload"], command, {}
    ) == {"uploaded": True}
    assert run.call_args.args[0] == [
        *command,
        "upload",
        "#upload",
        str(video),
        "--tab",
        "own-tab",
    ]


def test_upload_requires_explicit_tab(upload_environment):
    video, run = upload_environment
    with pytest.raises(SystemExit):
        upload_video([str(video)], ["opencli"], {})
    run.assert_not_called()


def test_upload_failure_is_not_retried(upload_environment):
    video, run = upload_environment
    run.side_effect = subprocess.CalledProcessError(1, "opencli")
    with pytest.raises(subprocess.CalledProcessError):
        upload_video([str(video), "--tab", "own-tab"], ["opencli"], {})
    run.assert_called_once()
    assert video.read_bytes() == b"video-fixture"


def test_upload_budget_rejects_large_video_before_dispatch(upload_environment):
    video, run = upload_environment
    with video.open("wb") as output:
        output.truncate(25 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="budget"):
        upload_video([str(video), "--tab", "own-tab"], ["opencli"], {})
    run.assert_not_called()
