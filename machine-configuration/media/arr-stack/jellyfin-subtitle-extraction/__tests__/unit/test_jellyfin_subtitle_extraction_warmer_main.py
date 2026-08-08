import importlib.util
import sys
from pathlib import Path

WARMER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "jellyfin_subtitle_extraction_warmer"
)
sys.path.insert(0, str(WARMER_PACKAGE_DIRECTORY_PATH))


def load_main_module():
    specification = importlib.util.spec_from_file_location(
        "jellyfin_subtitle_extraction_warmer_main",
        WARMER_PACKAGE_DIRECTORY_PATH / "__main__.py",
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


main_module = load_main_module()

JELLYFIN_DATA_DIRECTORY = "/home/zanoni/arr-stack/config/jellyfin/data/data"


def build_episode(identifier, name):
    return {
        "Id": identifier,
        "Name": name,
        "MediaSources": [
            {
                "Id": identifier,
                "MediaStreams": [
                    {
                        "Type": "Subtitle",
                        "Index": 2,
                        "Codec": "ass",
                        "IsTextSubtitleStream": True,
                        "IsExternal": False,
                    }
                ],
            }
        ],
    }


COLD_EPISODES = [
    build_episode(f"{index:032x}", f"Episode {index}") for index in range(1, 6)
]


def install_fake_jellyfin(
    monkeypatch, items, sessions_per_call, requested_paths, cache_is_warm=False
):
    monkeypatch.setattr(main_module, "list_video_items", lambda *_: items)
    monkeypatch.setattr(
        main_module, "list_active_sessions", lambda *_: sessions_per_call.pop(0)
    )
    monkeypatch.setattr(
        main_module,
        "request_body",
        lambda _base_url, _api_key, path: requested_paths.append(path),
    )
    monkeypatch.setattr(
        main_module,
        "unextracted_subtitle_streams_of_item",
        lambda item, _directory: (
            []
            if cache_is_warm
            else [
                {
                    "itemIdentifier": item["Id"],
                    "mediaSourceIdentifier": item["Id"],
                    "streamIndex": 2,
                    "requestedExtension": "ass",
                }
            ]
        ),
    )


def test_sweep_stops_at_its_item_budget(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch, COLD_EPISODES, [[]] * len(COLD_EPISODES), requested_paths
    )
    extracted_items, extracted_streams = main_module.sweep(
        "http://127.0.0.1:8096", "key", JELLYFIN_DATA_DIRECTORY, 2, 0
    )
    assert (extracted_items, extracted_streams) == (2, 2)
    assert len(requested_paths) == 2


def test_sweep_yields_the_disk_as_soon_as_playback_starts(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch,
        COLD_EPISODES,
        [[], [{"NowPlayingItem": {"Id": "watching"}}]],
        requested_paths,
    )
    extracted_items, extracted_streams = main_module.sweep(
        "http://127.0.0.1:8096", "key", JELLYFIN_DATA_DIRECTORY, 20, 0
    )
    assert (extracted_items, extracted_streams) == (1, 1)


def test_sweep_of_a_fully_extracted_library_asks_jellyfin_for_nothing(monkeypatch):
    requested_paths = []
    install_fake_jellyfin(
        monkeypatch, COLD_EPISODES, [], requested_paths, cache_is_warm=True
    )
    assert main_module.sweep(
        "http://127.0.0.1:8096", "key", JELLYFIN_DATA_DIRECTORY, 20, 0
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
        "http://127.0.0.1:8096", "key", JELLYFIN_DATA_DIRECTORY, 20, 0
    )
    assert extracted_items == len(COLD_EPISODES)
    assert extracted_streams == len(COLD_EPISODES) - 1
