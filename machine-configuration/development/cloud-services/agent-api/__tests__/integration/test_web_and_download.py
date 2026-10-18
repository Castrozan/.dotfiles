import sys
from types import ModuleType

import httpx
import pytest

from agent_api.contract import CapabilityError, OperationRequest
from agent_api.providers.downloading import DownloadProvider
from agent_api.providers.network import NetworkClient
from agent_api.providers.web import WebProvider


def test_http_download_follows_relative_redirect_and_retains_bytes(tmp_path):
    calls = []

    def respond(request):
        calls.append(request)
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": "/asset"})
        return httpx.Response(
            200,
            content=b"retained asset",
            headers={"content-type": "application/octet-stream"},
        )

    client = NetworkClient(10, httpx.Client(transport=httpx.MockTransport(respond)))
    request = OperationRequest("web.download", {"url": "https://example.com/start"})
    result = WebProvider().fetch(request, tmp_path, client, 1024)
    assert result["url"] == "https://example.com/asset"
    assert (tmp_path / result["artifact"]).read_bytes() == b"retained asset"
    assert len(calls) == 2


def test_web_extraction_preserves_text_and_refuses_oversized_response(tmp_path):
    client = NetworkClient(
        10,
        httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, text="document", headers={"content-type": "text/plain"}
                )
            )
        ),
    )
    request = OperationRequest("web.extract", {"url": "https://example.com"})
    result = WebProvider().fetch(request, tmp_path, client, 1024)
    assert result["markdown"] == "document"
    assert result["javascript_rendered"] is False
    (tmp_path / "download.bin").unlink()
    with pytest.raises(CapabilityError, match="response_too_large"):
        WebProvider().fetch(request, tmp_path, client, 2)


def test_downloader_keeps_one_item_disables_retries_and_passes_url_literally(
    tmp_path, monkeypatch
):
    options = {}

    class Downloader:
        def __init__(self, configuration):
            options.update(configuration)

        def __enter__(self):
            return self

        def __exit__(self, *arguments):
            pass

        def extract_info(self, url, download):
            assert url == "https://example.com/video"
            assert download is True
            (tmp_path / "media.mp4").write_bytes(b"video")
            return {"id": "fixture", "ext": "mp4"}

    module = ModuleType("yt_dlp")
    module.YoutubeDL = Downloader
    utilities = ModuleType("yt_dlp.utils")
    utilities.DownloadError = type("DownloadError", (Exception,), {})
    monkeypatch.setitem(sys.modules, "yt_dlp", module)
    monkeypatch.setitem(sys.modules, "yt_dlp.utils", utilities)
    request = OperationRequest("download.media", {"url": "https://example.com/video"})
    assert (
        DownloadProvider().execute(request, tmp_path, "id")["artifact"] == "media.mp4"
    )
    assert (
        options["retries"]
        == options["fragment_retries"]
        == options["extractor_retries"]
        == 0
    )
    assert options["playlist_items"] == "1"
    with pytest.raises(CapabilityError, match="artifact_too_large"):
        options["progress_hooks"][0]({"downloaded_bytes": 513 * 1024 * 1024})
