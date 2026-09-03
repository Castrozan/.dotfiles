import json
import re
from pathlib import Path

CONFIGURATION_DIRECTORY_PATH = Path(__file__).resolve().parents[2]


def load_desired_state(application, resource):
    desired_state_path = (
        CONFIGURATION_DIRECTORY_PATH
        / "desired-state"
        / application
        / f"{resource}.json"
    )
    return json.loads(desired_state_path.read_text())


def field_value(indexer, field_name):
    return next(
        field["value"] for field in indexer["fields"] if field["name"] == field_name
    )


def test_nyaa_only_returns_english_translated_anime_with_sonarr_titles():
    indexers = load_desired_state("prowlarr", "indexer")
    nyaa_indexer = next(indexer for indexer in indexers if indexer["name"] == "Nyaa.si")
    assert field_value(nyaa_indexer, "cat-id") == 3
    assert field_value(nyaa_indexer, "sonarr_compatibility") is True


def test_sonarr_receives_documentary_and_fallback_categories():
    applications = load_desired_state("prowlarr", "applications")
    sonarr_application = next(
        application for application in applications if application["name"] == "Sonarr"
    )
    sync_categories = field_value(sonarr_application, "syncCategories")
    assert 5080 in sync_categories
    assert 8000 in sync_categories
    assert field_value(sonarr_application, "apiKey") == "@SONARR_API_KEY@"


def test_sonarr_language_policy_accepts_dual_audio_without_foreign_markers():
    custom_formats = load_desired_state("sonarr", "customformat")
    english_subtitle_format = next(
        custom_format
        for custom_format in custom_formats
        if custom_format["name"] == "English Subtitle Group"
    )
    release_title_expression = english_subtitle_format["specifications"][0]["fields"][
        0
    ]["value"]
    assert re.search(
        release_title_expression,
        "[neoHEVC] NieA Under 7 [1080p x265 HEVC AAC] [Dual Audio]",
        re.IGNORECASE,
    )
    assert not re.search(
        release_title_expression,
        "Planet.Earth.S01E01.SWEDISH.720p.HDTV.x264-TX",
        re.IGNORECASE,
    )
    assert not re.search(
        release_title_expression,
        "Planet Earth S01E01 Hindi Dub 1080p BDRip",
        re.IGNORECASE,
    )
