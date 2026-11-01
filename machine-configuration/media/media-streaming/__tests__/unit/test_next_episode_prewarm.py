import importlib
import io
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest


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


@pytest.mark.parametrize(
    ("request_target", "expected_target"),
    [
        (ENCODED_EPISODE_TARGET, ENCODED_NEXT_EPISODE_TARGET),
        (PLAIN_EPISODE_TARGET, PLAIN_NEXT_EPISODE_TARGET),
        ("/config/stream/movie/tt1392170.json", None),
        ("/config/stream/series/kitsu%3A1%3A2.json", None),
        ("/config/playback/hash/0/5/1/1", None),
        ("/manifest.json", None),
    ],
)
def test_next_episode_target_only_advances_series_episode_streams(
    request_target, expected_target
):
    assert next_episode_prewarm.next_episode_target(request_target) == expected_target


def test_worker_warms_the_next_episode_once_per_target():
    warmed_targets = []
    warmed = threading.Event()

    def warm(target):
        warmed_targets.append(target)
        warmed.set()

    prewarmer = next_episode_prewarm.NextEpisodePrewarmer(warm)
    prewarmer.start()

    prewarmer.schedule_after(ENCODED_EPISODE_TARGET)
    assert warmed.wait(5)
    prewarmer.schedule_after(ENCODED_EPISODE_TARGET)
    prewarmer.wait_for_warming(ENCODED_NEXT_EPISODE_TARGET)

    assert warmed_targets == [ENCODED_NEXT_EPISODE_TARGET]


def test_foreground_request_waits_for_the_warming_of_its_own_episode():
    warming_started = threading.Event()
    release_warming = threading.Event()
    foreground_finished = threading.Event()

    def warm(_target):
        warming_started.set()
        release_warming.wait(5)

    prewarmer = next_episode_prewarm.NextEpisodePrewarmer(warm)
    prewarmer.start()
    prewarmer.schedule_after(ENCODED_EPISODE_TARGET)
    assert warming_started.wait(5)

    def foreground_request():
        prewarmer.wait_for_warming(ENCODED_NEXT_EPISODE_TARGET)
        foreground_finished.set()

    threading.Thread(target=foreground_request, daemon=True).start()

    assert not foreground_finished.wait(0.1)
    release_warming.set()
    assert foreground_finished.wait(5)


def test_untracked_foreground_request_does_not_wait():
    prewarmer = next_episode_prewarm.NextEpisodePrewarmer(lambda _target: None)

    prewarmer.wait_for_warming(ENCODED_NEXT_EPISODE_TARGET)


def test_full_queue_drops_targets_instead_of_growing():
    warmed_targets = []
    prewarmer = next_episode_prewarm.NextEpisodePrewarmer(warmed_targets.append)
    episode_count = next_episode_prewarm.MAXIMUM_QUEUED_TARGETS + 3

    for episode in range(1, episode_count + 1):
        prewarmer.schedule_after(f"/config/stream/series/tt1:1:{episode}.json")
    prewarmer.start()
    prewarmer.wait_for_warming(
        "/config/stream/series/tt1:1:"
        f"{next_episode_prewarm.MAXIMUM_QUEUED_TARGETS + 1}.json"
    )

    assert warmed_targets == [
        f"/config/stream/series/tt1:1:{episode}.json"
        for episode in range(2, next_episode_prewarm.MAXIMUM_QUEUED_TARGETS + 2)
    ]


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
