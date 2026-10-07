import io
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from shorts_browser_upload import upload_video


def upload_environment(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    configuration = tmp_path / ".pinchtab/config.json"
    configuration.parent.mkdir()
    configuration.write_text(json.dumps({"server": {"token": "fixture-credential"}}))
    video = tmp_path / "final.mp4"
    video.write_bytes(b"video-content")
    transport = Mock(return_value=io.BytesIO(b'{"files":1,"status":"ok"}'))
    monkeypatch.setattr("shorts_browser_upload.urlopen", transport)
    return video, transport


def test_upload_retains_mp4_extension_and_explicit_tab(monkeypatch, tmp_path):
    video, transport = upload_environment(monkeypatch, tmp_path)
    result = upload_video(
        [str(video), "--tab", "own-tab", "--selector", "#upload"],
        "http://127.0.0.1:9868",
    )
    request = transport.call_args.args[0]
    assert request.full_url == "http://127.0.0.1:9868/upload?tabId=own-tab"
    payload = json.loads(request.data)
    assert payload["selector"] == "#upload"
    staged = tmp_path / ".pinchtab/uploads" / payload["paths"][0]
    assert staged.suffix == ".mp4"
    assert staged.read_bytes() == video.read_bytes()
    assert request.headers["Authorization"] == "Bearer fixture-credential"
    assert "fixture-credential" not in json.dumps(result)


def test_upload_requires_explicit_tab(monkeypatch, tmp_path):
    video, transport = upload_environment(monkeypatch, tmp_path)
    with pytest.raises(SystemExit):
        upload_video([str(video)], "http://127.0.0.1:9868")
    transport.assert_not_called()


@pytest.mark.parametrize("invalid", ["oversized", "wrong-extension"])
def test_invalid_video_is_rejected_before_transport(monkeypatch, tmp_path, invalid):
    video, transport = upload_environment(monkeypatch, tmp_path)
    if invalid == "oversized":
        with video.open("wb") as output:
            output.truncate(25 * 1024 * 1024 + 1)
    else:
        video = video.rename(tmp_path / "video.bin")
    with pytest.raises(ValueError):
        upload_video([str(video), "--tab", "own-tab"], "http://127.0.0.1:9868")
    transport.assert_not_called()
    assert not (tmp_path / ".pinchtab/uploads").exists()


def test_ambiguous_upload_retains_video_for_lazy_browser_reads(monkeypatch, tmp_path):
    video, transport = upload_environment(monkeypatch, tmp_path)
    sandbox = tmp_path / ".pinchtab/uploads"
    sandbox.mkdir()
    preserved = sandbox / "existing.mp4"
    preserved.write_bytes(b"existing")
    transport.side_effect = OSError("transport failed")
    with pytest.raises(RuntimeError, match="ambiguous"):
        upload_video([str(video), "--tab", "own-tab"], "http://127.0.0.1:9868")
    assert preserved.read_bytes() == b"existing"
    staged = list(sandbox.glob("pinchtab-upload-shorts-*/video.mp4"))
    assert len(staged) == 1
    assert staged[0].read_bytes() == video.read_bytes()
