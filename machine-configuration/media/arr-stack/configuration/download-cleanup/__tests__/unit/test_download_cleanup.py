from unittest.mock import Mock

import pytest

from download_cleanup.domain import Media, parse_event
from download_cleanup.ledger import Ledger
from download_cleanup_test_support import worker_for


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "cleanup.sqlite")


@pytest.fixture
def media():
    return Media("sonarr", 12, 1234, "Example", "/data/media/tv/Example")


def test_full_deletion_removes_only_recorded_hashes_and_refreshes_jellyfin(
    ledger, media
):
    owned_hash = "a" * 40
    other_hash = "b" * 40
    ledger.record_download(media, owned_hash)
    ledger.enqueue(media)
    torrents = Mock()
    torrents.list.side_effect = [
        [
            {"hash": owned_hash, "content_path": "/data/torrents/Example.mkv"},
            {"hash": other_hash, "content_path": "/data/torrents/Other.mkv"},
        ],
        [{"hash": other_hash, "content_path": "/data/torrents/Other.mkv"}],
    ]
    worker = worker_for(ledger, torrents)
    worker.process(media)
    torrents.delete.assert_called_once_with([owned_hash])
    worker.jellyfin.cleanup.assert_called_once_with(media)
    assert ledger.pending() == []


@pytest.mark.parametrize(
    "event_type", ["EpisodeFileDelete", "MovieFileDelete", "Rename"]
)
def test_file_changes_do_not_authorize_title_cleanup(event_type):
    assert parse_event("sonarr", {"eventType": event_type}) is None


def test_record_only_delete_does_not_authorize_cleanup():
    assert (
        parse_event("sonarr", {"eventType": "SeriesDelete", "deletedFiles": False})
        is None
    )


def test_string_true_does_not_authorize_cleanup():
    assert (
        parse_event("sonarr", {"eventType": "SeriesDelete", "deletedFiles": "true"})
        is None
    )


def test_radarr_native_folder_path_is_used():
    event = parse_event(
        "radarr",
        {
            "eventType": "MovieDelete",
            "deletedFiles": True,
            "movie": {
                "id": 7,
                "tmdbId": 123,
                "title": "Film",
                "folderPath": "/data/media/movies/Film",
            },
        },
    )
    assert event.media == Media("radarr", 7, 123, "Film", "/data/media/movies/Film")


def test_network_failure_survives_restart_and_retries(ledger, media, tmp_path):
    ledger.record_download(media, "a" * 40)
    ledger.enqueue(media)
    torrents = Mock()
    torrents.list.side_effect = OSError("offline")
    worker = worker_for(ledger, torrents)
    worker.run_pending()
    restarted = Ledger(tmp_path / "cleanup.sqlite")
    assert restarted.pending(now=10**12) == [media]
    torrents.delete.assert_not_called()
    worker.jellyfin.cleanup.assert_not_called()


def test_readded_title_cancels_old_deletion(ledger, media):
    ledger.record_download(media, "a" * 40)
    ledger.enqueue(media)
    worker = worker_for(ledger, Mock())
    worker.media_clients["sonarr"].exists.return_value = True
    worker.process(media)
    worker.torrents.delete.assert_not_called()
    assert ledger.pending() == []
    assert ledger.downloads(media)[0][0] == "a" * 40


def test_retained_library_blocks_payload_deletion(ledger, media):
    ledger.record_download(media, "a" * 40)
    ledger.enqueue(media)
    worker = worker_for(ledger, Mock())
    worker.filesystem.library_exists.return_value = True
    with pytest.raises(RuntimeError, match="library"):
        worker.process(media)
    worker.torrents.delete.assert_not_called()


def test_shared_torrent_is_preserved(ledger, media):
    other = Media("sonarr", 13, 1235, "Other", "/data/media/tv/Other")
    ledger.record_download(media, "a" * 40)
    ledger.record_download(other, "a" * 40)
    ledger.enqueue(media)
    torrents = Mock()
    torrents.list.return_value = [
        {"hash": "a" * 40, "content_path": "/data/torrents/Shared"}
    ]
    worker = worker_for(ledger, torrents)
    worker.media_clients["sonarr"].exists.side_effect = [False, True]
    with pytest.raises(RuntimeError, match="shared"):
        worker.process(media)
    torrents.delete.assert_not_called()


def test_overlapping_unrelated_torrent_is_preserved(ledger, media):
    ledger.record_download(media, "a" * 40)
    ledger.enqueue(media)
    torrents = Mock()
    torrents.list.return_value = [
        {"hash": "a" * 40, "content_path": "/data/torrents/Shared"},
        {"hash": "b" * 40, "content_path": "/data/torrents/Shared/Other.mkv"},
    ]
    worker = worker_for(ledger, torrents)
    with pytest.raises(ValueError, match="overlap"):
        worker.process(media)
    torrents.delete.assert_not_called()


def test_file_deletion_must_be_observed_before_completion(ledger, media):
    ledger.record_download(media, "a" * 40)
    ledger.enqueue(media)
    torrents = Mock()
    torrents.list.side_effect = [
        [{"hash": "a" * 40, "content_path": "/data/torrents/Example.mkv"}],
        [],
    ]
    worker = worker_for(ledger, torrents)
    worker.filesystem.download_exists.return_value = True
    with pytest.raises(RuntimeError, match="files"):
        worker.process(media)
    assert ledger.downloads(media) == [("a" * 40, "/data/torrents/Example.mkv")]
    assert ledger.pending() == [media]
    worker.jellyfin.cleanup.assert_not_called()


def test_late_grab_reopens_completed_deletion(ledger, media):
    ledger.enqueue(media)
    ledger.complete(media, ledger.revision(media))
    ledger.record_download(media, "a" * 40)
    assert ledger.pending() == [media]


def test_grab_during_cleanup_cannot_be_discarded_by_completion(ledger, media):
    ledger.record_download(media, "a" * 40)
    ledger.enqueue(media)
    revision = ledger.revision(media)
    ledger.record_download(media, "b" * 40)
    assert not ledger.complete(media, revision)
    assert ledger.pending() == [media]
    assert {value[0] for value in ledger.downloads(media)} == {"a" * 40, "b" * 40}


def test_different_provider_cannot_inherit_old_hashes(ledger, media):
    ledger.record_download(media, "a" * 40)
    replacement = Media(
        "sonarr", media.identifier, 5555, "Other", "/data/media/tv/Other"
    )
    assert ledger.downloads(replacement) == []
