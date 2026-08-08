import sys
from pathlib import Path

WARMER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "jellyfin_subtitle_extraction_warmer"
)
sys.path.insert(0, str(WARMER_PACKAGE_DIRECTORY_PATH))

import subtitle_extraction_cache

JELLYFIN_DATA_DIRECTORY = "/home/zanoni/arr-stack/config/jellyfin/data/data"
FATE_ZERO_EPISODE_IDENTIFIER = "d99bedfb85ec4e43894ab517be075d51"

FATE_ZERO_EPISODE = {
    "Id": FATE_ZERO_EPISODE_IDENTIFIER,
    "Name": "Master and Servant",
    "MediaSources": [
        {
            "Id": FATE_ZERO_EPISODE_IDENTIFIER,
            "MediaStreams": [
                {"Type": "Video", "Index": 0},
                {"Type": "Audio", "Index": 1},
                {
                    "Type": "Subtitle",
                    "Index": 2,
                    "Codec": "ass",
                    "IsTextSubtitleStream": True,
                    "IsExternal": False,
                },
                {
                    "Type": "Subtitle",
                    "Index": 3,
                    "Codec": "subrip",
                    "IsTextSubtitleStream": True,
                    "IsExternal": False,
                },
                {
                    "Type": "Subtitle",
                    "Index": 4,
                    "Codec": "pgssub",
                    "IsTextSubtitleStream": False,
                    "IsExternal": False,
                },
                {
                    "Type": "Subtitle",
                    "Index": 5,
                    "Codec": "subrip",
                    "IsTextSubtitleStream": True,
                    "IsExternal": True,
                },
            ],
        }
    ],
}


def test_cache_path_matches_the_layout_jellyfin_writes_on_disk():
    assert (
        subtitle_extraction_cache.extraction_cache_path(
            JELLYFIN_DATA_DIRECTORY, FATE_ZERO_EPISODE_IDENTIFIER, 5, "ass"
        )
        == f"{JELLYFIN_DATA_DIRECTORY}/subtitles/d9"
        "/d99bedfb-85ec-4e43-894a-b517be075d51/5.ass"
    )


def test_cache_path_accepts_an_already_dashed_identifier():
    assert subtitle_extraction_cache.extraction_cache_path(
        JELLYFIN_DATA_DIRECTORY, "d99bedfb-85ec-4e43-894a-b517be075d51", 2, "ass"
    ) == subtitle_extraction_cache.extraction_cache_path(
        JELLYFIN_DATA_DIRECTORY, FATE_ZERO_EPISODE_IDENTIFIER, 2, "ass"
    )


def test_only_ass_and_ssa_keep_their_own_extraction_extension():
    assert subtitle_extraction_cache.extraction_file_extension_for_codec("ASS") == "ass"
    assert subtitle_extraction_cache.extraction_file_extension_for_codec("ssa") == "ssa"
    assert (
        subtitle_extraction_cache.extraction_file_extension_for_codec("subrip") == "srt"
    )
    assert subtitle_extraction_cache.extraction_file_extension_for_codec(None) == "srt"


def test_graphical_and_external_subtitle_streams_are_never_extracted():
    streams = subtitle_extraction_cache.embedded_text_subtitle_streams(
        FATE_ZERO_EPISODE["MediaSources"][0]
    )
    assert [stream["Index"] for stream in streams] == [2, 3]


def test_an_item_with_a_warm_cache_reports_nothing_to_extract():
    assert (
        subtitle_extraction_cache.unextracted_subtitle_streams_of_item(
            FATE_ZERO_EPISODE,
            JELLYFIN_DATA_DIRECTORY,
            cache_path_exists=lambda _: True,
        )
        == []
    )


def test_an_item_with_a_cold_cache_reports_every_embedded_text_stream():
    unextracted_streams = (
        subtitle_extraction_cache.unextracted_subtitle_streams_of_item(
            FATE_ZERO_EPISODE,
            JELLYFIN_DATA_DIRECTORY,
            cache_path_exists=lambda _: False,
        )
    )
    assert [stream["streamIndex"] for stream in unextracted_streams] == [2, 3]
    assert [stream["requestedExtension"] for stream in unextracted_streams] == [
        "ass",
        "srt",
    ]


def test_request_path_targets_the_jellyfin_subtitle_stream_route():
    unextracted_stream = subtitle_extraction_cache.unextracted_subtitle_streams_of_item(
        FATE_ZERO_EPISODE, JELLYFIN_DATA_DIRECTORY, cache_path_exists=lambda _: False
    )[0]
    assert (
        subtitle_extraction_cache.subtitle_stream_request_path(unextracted_stream)
        == f"/Videos/{FATE_ZERO_EPISODE_IDENTIFIER}"
        f"/{FATE_ZERO_EPISODE_IDENTIFIER}/Subtitles/2/Stream.ass"
    )


def test_playback_anywhere_on_the_server_counts_as_watching():
    assert not subtitle_extraction_cache.someone_is_watching([])
    assert not subtitle_extraction_cache.someone_is_watching(
        [{"UserName": "lucas", "NowPlayingItem": None}]
    )
    assert subtitle_extraction_cache.someone_is_watching(
        [{"UserName": "lucas"}, {"UserName": "joshen", "NowPlayingItem": {"Id": "x"}}]
    )
