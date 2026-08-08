import importlib.util
import sys
from pathlib import Path

WARMER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "jellyfin_subtitle_extraction_warmer"
)
sys.path.insert(0, str(WARMER_PACKAGE_DIRECTORY_PATH))

JELLYFIN_DATA_DIRECTORY = "/home/zanoni/arr-stack/config/jellyfin/data/data"
JELLYFIN_BASE_URL = "http://127.0.0.1:8096"
WATCHING_SESSIONS = [{"NowPlayingItem": {"Id": "episode"}}]


def load_main_module():
    specification = importlib.util.spec_from_file_location(
        "jellyfin_subtitle_extraction_warmer_main",
        WARMER_PACKAGE_DIRECTORY_PATH / "__main__.py",
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


main_module = load_main_module()


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


def install_warmer_environment(monkeypatch):
    monkeypatch.setenv(
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BASE_URL", JELLYFIN_BASE_URL
    )
    monkeypatch.setenv(
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_API_KEY_FILE", "/run/agenix/key"
    )
    monkeypatch.setenv(
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_DATA_DIRECTORY", JELLYFIN_DATA_DIRECTORY
    )
    monkeypatch.setenv("JELLYFIN_SUBTITLE_EXTRACTION_WARMER_ITEM_BUDGET", "20")
    monkeypatch.setenv("JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BUSY_ITEM_BUDGET", "3")
    monkeypatch.setenv("JELLYFIN_SUBTITLE_EXTRACTION_WARMER_PAUSE_SECONDS", "0")
    monkeypatch.setenv("JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_POLL_SECONDS", "30")
    monkeypatch.setenv("JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_WAIT_SECONDS", "1200")
    monkeypatch.setattr(main_module, "read_api_key", lambda _: "key")
    monkeypatch.setattr(main_module, "jellyfin_is_reachable", lambda *_: True)
