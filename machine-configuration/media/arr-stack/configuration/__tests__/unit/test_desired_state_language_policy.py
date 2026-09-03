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


def test_sonarr_separates_original_language_from_english_caption_profiles():
    custom_formats = load_desired_state("sonarr", "customformat")
    original_language_format = next(
        custom_format
        for custom_format in custom_formats
        if custom_format["name"] == "Original Language"
    )
    original_language_value = original_language_format["specifications"][0]["fields"][
        0
    ]["value"]
    assert original_language_value == -2

    profiles = load_desired_state("sonarr", "qualityprofile")
    profiles_by_name = {profile["name"]: profile for profile in profiles}
    original_language_scores = profiles_by_name["HD - Original Language"][
        "formatScores"
    ]
    english_caption_scores = profiles_by_name["HD - English Captions"]["formatScores"]
    assert original_language_scores["Original Language"] == 50
    assert "English Subtitle Group" not in original_language_scores
    assert english_caption_scores["English Subtitle Group"] == 50
    assert "Original Language" not in english_caption_scores


def test_jellyseerr_routes_standard_and_anime_requests_to_distinct_profiles():
    routes = load_desired_state("jellyseerr", "sonarr")
    route = next(route for route in routes if route["name"] == "Sonarr")
    assert route["standardProfileName"] == "HD - Original Language"
    assert route["animeProfileName"] == "HD - English Captions"


def test_limetorrents_uses_current_download_link_fields():
    indexers = load_desired_state("prowlarr", "indexer")
    limetorrents_indexer = next(
        indexer for indexer in indexers if indexer["name"] == "LimeTorrents"
    )
    field_names = {field["name"] for field in limetorrents_indexer["fields"]}
    assert "primarydownloadlink" in field_names
    assert "fallbackdownloadlink" in field_names
    assert "downloadlink" not in field_names
    assert "downloadlink2" not in field_names
