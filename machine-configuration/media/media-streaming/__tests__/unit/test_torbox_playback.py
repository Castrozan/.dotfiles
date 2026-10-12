import importlib
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))
torbox_playback = importlib.import_module("torbox_playback")
comet_stream_adapter = importlib.import_module("comet_stream_adapter")


@pytest.mark.parametrize("include_body", [True, False])
def test_relays_range_requests_without_exposing_credentials_or_buffering_video(
    include_body, monkeypatch
):
    requested = []
    read_sizes = []
    sent_headers = {}
    sent_statuses = []
    video = b"v" * (torbox_playback.MEDIA_CHUNK_BYTES + 7)

    class Upstream(io.BytesIO):
        status = 206
        headers = {
            "Content-Type": "video/x-matroska",
            "Content-Length": str(len(video)),
            "Content-Range": f"bytes 1-{len(video)}/{len(video) + 1}",
            "Accept-Ranges": "bytes",
        }

        def read(self, size):
            read_sizes.append(size)
            return super().read(size)

    def open_request(request, timeout):
        requested.append(request)
        assert timeout == 30
        return Upstream(video)

    monkeypatch.setattr(torbox_playback.urllib.request, "urlopen", open_request)
    handler = SimpleNamespace(
        headers={"Range": "bytes=1-"},
        wfile=io.BytesIO(),
        send_response=sent_statuses.append,
        send_header=sent_headers.__setitem__,
        _send_cors_headers=lambda: None,
        end_headers=lambda: None,
    )
    response = comet_stream_adapter.CometResponse(
        302,
        "application/octet-stream",
        None,
        "https://media.example/episode.mkv?token=secret",
        b"",
    )
    assert torbox_playback.relay_torbox_playback(handler, response, include_body)
    assert requested[0].get_header("Range") == "bytes=1-"
    assert requested[0].get_method() == ("GET" if include_body else "HEAD")
    assert sent_statuses == [206]
    assert "Location" not in sent_headers
    assert all("secret" not in value for value in sent_headers.values())
    assert handler.wfile.getvalue() == (video if include_body else b"")
    assert all(size == torbox_playback.MEDIA_CHUNK_BYTES for size in read_sizes)


def test_media_failures_do_not_expose_the_authenticated_url(monkeypatch):
    def fail(request, timeout):
        raise RuntimeError(request.full_url)

    monkeypatch.setattr(torbox_playback.urllib.request, "urlopen", fail)
    handler = SimpleNamespace(headers={})
    response = comet_stream_adapter.CometResponse(
        302,
        "application/octet-stream",
        None,
        "https://media.example/episode.mkv?token=secret",
        b"",
    )
    with pytest.raises(RuntimeError, match="^TorBox media request failed$"):
        torbox_playback.relay_torbox_playback(handler, response, True)
