import importlib
import io
import sys
from pathlib import Path
from types import SimpleNamespace


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))
next_episode_prewarm = importlib.import_module("next_episode_prewarm")
comet_proxy = importlib.import_module("comet_proxy")
comet_stream_adapter = importlib.import_module("comet_stream_adapter")

ENCODED_EPISODE_TARGET = "/config/stream/series/tt13293588%3A1%3A2.json"
ENCODED_NEXT_EPISODE_TARGET = "/config/stream/series/tt13293588%3A1%3A3.json"
PLAIN_EPISODE_TARGET = "/config/stream/series/tt13293588:1:9.json"
PLAIN_NEXT_EPISODE_TARGET = "/config/stream/series/tt13293588:1:10.json"


def test_proxy_waits_for_warming_before_fetching_and_schedules_afterwards():
    events = []

    class Prewarmer:
        def wait_for_warming(self, target):
            events.append(("wait", target))

        def schedule_after(self, target):
            events.append(("schedule", target))

    class Adapter:
        def response(self, target, _origin):
            events.append(("fetch", target))
            return comet_stream_adapter.CometResponse(
                200, "application/json", None, None, b"{}"
            )

    handler = SimpleNamespace(
        headers={"Host": "stream.example.com"},
        comet_adapter=Adapter(),
        next_episode_prewarmer=Prewarmer(),
        wfile=io.BytesIO(),
        send_response=lambda _status: None,
        send_header=lambda _name, _value: None,
        end_headers=lambda: None,
        _send_cors_headers=lambda: None,
    )

    comet_proxy.proxy_comet_request(handler, ENCODED_EPISODE_TARGET, True)

    assert events == [
        ("wait", ENCODED_EPISODE_TARGET),
        ("fetch", ENCODED_EPISODE_TARGET),
        ("schedule", ENCODED_EPISODE_TARGET),
    ]


def test_failed_warming_releases_waiting_requests_and_keeps_the_worker_alive():
    warmed_targets = []

    def warm(target):
        warmed_targets.append(target)
        if target == ENCODED_NEXT_EPISODE_TARGET:
            raise RuntimeError("Comet upstream request failed")

    prewarmer = next_episode_prewarm.NextEpisodePrewarmer(warm)
    prewarmer.start()

    prewarmer.schedule_after(ENCODED_EPISODE_TARGET)
    prewarmer.wait_for_warming(ENCODED_NEXT_EPISODE_TARGET)
    prewarmer.schedule_after(PLAIN_EPISODE_TARGET)
    prewarmer.wait_for_warming(PLAIN_NEXT_EPISODE_TARGET)

    assert warmed_targets == [ENCODED_NEXT_EPISODE_TARGET, PLAIN_NEXT_EPISODE_TARGET]
