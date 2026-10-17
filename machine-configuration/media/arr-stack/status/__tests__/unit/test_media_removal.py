import importlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/arr_media"))
removal = importlib.import_module("media_removal")


@pytest.mark.parametrize(
    "envelope",
    [
        None,
        "invalid",
        "[]",
        '{"user_id":"owner"}',
        '{"source":"discord","user_id":"guest","content":"owner"}',
    ],
)
def test_unverified_sender_cannot_remove_media(monkeypatch, envelope):
    monkeypatch.setenv("ARR_MEDIA_OPERATOR_DISCORD_USER_ID", "owner")
    monkeypatch.delenv("CLAWDE_CHANNEL_PROMPT", raising=False)
    if envelope is not None:
        monkeypatch.setenv("CLAWDE_CHANNEL_PROMPT", envelope)
    with pytest.raises(ValueError, match="operator"):
        removal.authorize_media_removal()


def test_verified_discord_owner_is_authorized(monkeypatch):
    monkeypatch.setenv("ARR_MEDIA_OPERATOR_DISCORD_USER_ID", "owner")
    monkeypatch.setenv(
        "CLAWDE_CHANNEL_PROMPT", json.dumps({"source": "discord", "user_id": "owner"})
    )
    removal.authorize_media_removal()


@pytest.fixture
def media(monkeypatch):
    client = Mock(api_key="secret")
    client.details.return_value = {
        "id": 769,
        "mediaInfo": {
            "id": 79,
            "tmdbId": 769,
            "mediaType": "movie",
            "externalServiceId": 43,
            "externalServiceSlug": "769",
        },
    }
    library = Mock()
    library.item.side_effect = [
        {"id": 43, "tmdbId": 769, "path": "/data/media/movies/Goodfellas (1990)"},
        None,
    ]
    monkeypatch.setattr(removal, "load_media_library", lambda *_: library)
    administrator = Mock()
    monkeypatch.setattr(removal, "JellyseerrMedia", lambda *_: administrator)
    return client, library, administrator


def test_removal_uses_native_file_deletion_and_verifies_disappearance(media):
    client, library, administrator = media
    result = removal.remove_media(client, "/stack", "movie", 769)
    administrator.request.assert_called_once_with("DELETE", "/media/79/file?is4k=false")
    assert library.item.call_count == 2
    assert result["result"] == "media_removed"
    assert result["library_files"] == "deletion_requested"


@pytest.mark.parametrize(
    "record",
    [
        {"id": 43, "tmdbId": 769, "path": "/data/media/movies-private/Goodfellas"},
        {"id": 43, "tmdbId": 769, "path": "/data/media/movies/../movies-private/x"},
        {"id": 43, "tmdbId": 9366, "path": "/data/media/movies/Donnie Brasco"},
        {"id": 44, "tmdbId": 769, "path": "/data/media/movies/Goodfellas"},
    ],
)
def test_private_or_mismatched_media_is_never_deleted(media, record):
    client, library, administrator = media
    library.item.side_effect = None
    library.item.return_value = record
    with pytest.raises(ValueError):
        removal.remove_media(client, "/stack", "movie", 769)
    administrator.request.assert_not_called()


def test_missing_library_entry_is_a_safe_noop(media):
    client, library, administrator = media
    library.item.side_effect = [None]
    assert (
        removal.remove_media(client, "/stack", "movie", 769)["result"] == "not_present"
    )
    administrator.request.assert_not_called()


def test_unconfirmed_deletion_never_reports_success(media):
    client, library, _ = media
    library.item.side_effect = None
    library.item.return_value = {
        "id": 43,
        "tmdbId": 769,
        "path": "/data/media/movies/Goodfellas",
    }
    with pytest.raises(ValueError, match="unconfirmed"):
        removal.remove_media(client, "/stack", "movie", 769)


def test_tv_uses_tvdb_identity_and_public_tv_root(media):
    client, library, administrator = media
    client.details.return_value = {
        "id": 1396,
        "externalIds": {"tvdbId": 81189},
        "mediaInfo": {
            "id": 80,
            "tmdbId": 1396,
            "mediaType": "tv",
            "externalServiceId": 7,
        },
    }
    library.item.side_effect = [
        {"id": 7, "tvdbId": 81189, "path": "/data/media/tv/Breaking Bad"},
        None,
    ]
    assert (
        removal.remove_media(client, "/stack", "tv", 1396)["result"] == "media_removed"
    )
    administrator.request.assert_called_once_with("DELETE", "/media/80/file?is4k=false")
