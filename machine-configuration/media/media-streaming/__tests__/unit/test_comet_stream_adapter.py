import importlib
import json
import sys
from pathlib import Path


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

comet_stream_adapter = importlib.import_module("comet_stream_adapter")


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
        "http://100.64.0.1:43214", request
    )

    response = adapter.response("/stream/movie/tt15239678.json")

    assert requested_urls == ["http://100.64.0.1:43214/stream/movie/tt15239678.json"]
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
        "http://100.64.0.1:43214", lambda url: expected_response
    )

    assert adapter.response("/manifest.json") is expected_response
