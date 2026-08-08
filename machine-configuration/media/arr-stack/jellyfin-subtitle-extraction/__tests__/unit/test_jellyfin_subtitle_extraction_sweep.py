import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jellyfin_subtitle_extraction_test_doubles import (
    COLD_EPISODES,
    JELLYFIN_BASE_URL,
    JELLYFIN_DATA_DIRECTORY,
    WATCHING_SESSIONS,
    install_fake_jellyfin,
    main_module,
)


def test_sweep_stops_at_its_item_budget(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch, COLD_EPISODES, [[]] * len(COLD_EPISODES), requested_paths
    )
    extracted_items, extracted_streams = main_module.sweep(
        JELLYFIN_BASE_URL, "key", JELLYFIN_DATA_DIRECTORY, 2, 0
    )
    assert (extracted_items, extracted_streams) == (2, 2)
    assert len(requested_paths) == 2


def test_sweep_yields_the_disk_as_soon_as_playback_starts(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch, COLD_EPISODES, [[], WATCHING_SESSIONS], requested_paths
    )
    extracted_items, extracted_streams = main_module.sweep(
        JELLYFIN_BASE_URL, "key", JELLYFIN_DATA_DIRECTORY, 20, 0
    )
    assert (extracted_items, extracted_streams) == (1, 1)


def test_a_sweep_that_does_not_yield_keeps_extracting_through_playback(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch,
        COLD_EPISODES,
        [WATCHING_SESSIONS] * len(COLD_EPISODES),
        requested_paths,
    )
    extracted_items, extracted_streams = main_module.sweep(
        JELLYFIN_BASE_URL,
        "key",
        JELLYFIN_DATA_DIRECTORY,
        3,
        0,
        yield_to_playback=False,
    )
    assert (extracted_items, extracted_streams) == (3, 3)


def test_sweep_of_a_fully_extracted_library_asks_jellyfin_for_nothing(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch, COLD_EPISODES, [], requested_paths, cache_is_warm=True
    )
    assert main_module.sweep(
        JELLYFIN_BASE_URL, "key", JELLYFIN_DATA_DIRECTORY, 20, 0
    ) == (0, 0)
    assert requested_paths == []


def test_a_failed_extraction_does_not_abort_the_rest_of_the_sweep(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch, COLD_EPISODES, [[]] * len(COLD_EPISODES), requested_paths
    )

    def fail_once(_base_url, _api_key, path):
        if len(requested_paths) == 0:
            requested_paths.append(path)
            raise OSError("extraction timed out")
        requested_paths.append(path)

    monkeypatch.setattr(main_module, "request_body", fail_once)
    extracted_items, extracted_streams = main_module.sweep(
        JELLYFIN_BASE_URL, "key", JELLYFIN_DATA_DIRECTORY, 20, 0
    )
    assert extracted_items == len(COLD_EPISODES)
    assert extracted_streams == len(COLD_EPISODES) - 1
