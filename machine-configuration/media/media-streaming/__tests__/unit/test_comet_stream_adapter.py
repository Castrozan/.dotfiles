import base64
import importlib
import json
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

comet_stream_adapter = importlib.import_module("comet_stream_adapter")
managed_profile = importlib.import_module("managed_profile")
CONFIGURATION = {"cachedOnly": True, "debridService": "torbox", "enableTorrent": False}


def test_normalizes_peer_discovery_sources():
    response_body = json.dumps(
        {
            "streams": [
                {
                    "infoHash": "A" * 40,
                    "sources": [
                        "udp://tracker.example:80/announce",
                        "https://tracker.example/announce",
                        "tracker:udp://tracker.example:80/announce",
                        "invalid-source",
                    ],
                }
            ]
        }
    ).encode()
    requested_urls = []

    def request(url):
        requested_urls.append(url)
        return comet_stream_adapter.CometResponse(
            200, "application/json", "max-age=30", None, response_body
        )

    adapter = comet_stream_adapter.CometStreamAdapter(
        "http://100.64.0.1:43214", CONFIGURATION, "test-secret", request
    )

    response = adapter.response(
        "/stream/movie/tt15239678.json", "https://stream.example"
    )

    assert requested_urls[0].endswith("/stream/movie/tt15239678.json")
    private_configuration = json.loads(
        base64.b64decode(requested_urls[0].split("/")[3])
    )
    assert private_configuration["debridApiKey"] == "test-secret"
    assert private_configuration["cachedOnly"] is True
    assert private_configuration["enableTorrent"] is False
    assert json.loads(response.body)["streams"][0]["sources"] == [
        "tracker:udp://tracker.example:80/announce",
        "tracker:https://tracker.example/announce",
        f"dht:{'a' * 40}",
    ]


def test_preserves_non_stream_responses():
    expected_response = comet_stream_adapter.CometResponse(
        200, "application/json", "max-age=30", None, b'{"id":"stremio.comet.fast"}'
    )
    adapter = comet_stream_adapter.CometStreamAdapter(
        "http://100.64.0.1:43214",
        CONFIGURATION,
        "test-secret",
        lambda url: expected_response,
    )

    assert (
        adapter.response("/manifest.json", "https://stream.example")
        is expected_response
    )


def test_keeps_the_torbox_key_out_of_playback_links_and_preserves_episode_scope():
    requested_urls = []

    def request(url):
        requested_urls.append(url)
        encoded_configuration = urllib.parse.urlsplit(url).path.split("/")[1]
        playback_url = f"http://100.64.0.1:43214/{encoded_configuration}/playback/{'a' * 40}/0/n/1/2?name=Episode&media_type=series"
        return comet_stream_adapter.CometResponse(
            200,
            "application/json",
            None,
            None,
            json.dumps(
                {"streams": [{"name": "TorBox Cached", "url": playback_url}]}
            ).encode(),
        )

    adapter = comet_stream_adapter.CometStreamAdapter(
        "http://100.64.0.1:43214", CONFIGURATION, "test-secret", request
    )
    response = adapter.response(
        "/old-configuration/stream/series/tt2560140%3A1%3A2.json",
        "https://stream.example",
    )
    playback_url = json.loads(response.body)["streams"][0]["url"]
    encoded_configuration = urllib.parse.urlsplit(playback_url).path.split("/")[2]
    assert json.loads(base64.b64decode(encoded_configuration)) == CONFIGURATION
    assert "test-secret" not in response.body.decode()
    assert "sources" not in json.loads(response.body)["streams"][0]
    adapter.response(
        urllib.parse.urlsplit(playback_url).path.removeprefix("/comet")
        + "?name=Episode&media_type=series",
        "https://stream.example",
    )
    assert requested_urls[-1].endswith(
        f"/playback/{'a' * 40}/0/n/1/2?name=Episode&media_type=series"
    )
    private_configuration = json.loads(
        base64.b64decode(urllib.parse.urlsplit(requested_urls[-1]).path.split("/")[1])
    )
    assert private_configuration["debridApiKey"] == "test-secret"


def test_playback_redirect_is_returned_without_downloading_video():
    requests = []

    class RedirectHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(302)
            self.send_header(
                "Location", f"http://127.0.0.1:{self.server.server_port}/episode.mkv"
            )
            self.end_headers()

        def log_message(self, format_string, *arguments):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        response = comet_stream_adapter.fetch_comet_response(
            f"http://127.0.0.1:{server.server_port}/playback"
        )
        assert response.status == 302
        assert response.location == f"http://127.0.0.1:{server.server_port}/episode.mkv"
        assert requests == ["/playback"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_managed_profile_offers_only_cached_torbox_sources():
    addons = managed_profile.MANAGED_PROFILE_CONFIGURATION["managedAddons"]
    assert len(addons) == 1
    configuration = addons[0]["configuration"]
    assert configuration["debridService"] == "torbox"
    assert configuration["cachedOnly"] is True
    assert configuration["enableTorrent"] is False
    assert configuration["maxResultsPerResolution"] == 1
    assert "debridApiKey" not in configuration


def test_configuration_pages_cannot_reveal_the_server_key():
    requested_urls = []
    adapter = comet_stream_adapter.CometStreamAdapter(
        "http://100.64.0.1:43214", CONFIGURATION, "test-secret", requested_urls.append
    )
    assert (
        adapter.response(
            "/old-configuration/configure", "https://stream.example"
        ).status
        == 404
    )
    assert requested_urls == []


def test_upstream_failures_do_not_reveal_private_configuration():
    def request(url):
        raise RuntimeError(url)

    adapter = comet_stream_adapter.CometStreamAdapter(
        "http://100.64.0.1:43214", CONFIGURATION, "test-secret", request
    )
    try:
        adapter.response("/stream/series/tt2560140:1:1.json", "https://stream.example")
    except RuntimeError as error:
        assert str(error) == "Comet upstream request failed"
    else:
        raise AssertionError("Upstream failure was not raised")
