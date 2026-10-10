import json
from unittest.mock import Mock

import pytest

from download_cleanup.clients import MediaClient
from download_cleanup.domain import Media
from download_cleanup.ledger import Ledger
from download_cleanup.transport import HttpFailure
from download_cleanup_test_support import worker_for


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "provider-retention.sqlite")


@pytest.fixture
def media():
    return Media("radarr", 31, 10331, "Deleted", "/data/media/movies/Previous location")


def create_restored_media_client(app, provider_identifier):
    client = MediaClient("http://127.0.0.1/api/v3", "key", app)
    provider_field = "tmdbId" if app == "radarr" else "tvdbId"
    current = {"id": 32, provider_field: provider_identifier}
    responses = {
        f"/{client.resource}": json.dumps([current]).encode(),
        f"/{client.resource}/32": json.dumps(current).encode(),
    }

    def response(path):
        if path not in responses:
            raise HttpFailure(404)
        return responses[path]

    client.transport = Mock()
    client.transport.request.side_effect = response
    return client


def create_torrent_client(download_hash):
    client = Mock()
    client.list.side_effect = [
        [{"hash": download_hash, "content_path": "/data/torrents/Example.mkv"}],
        [],
    ]
    return client


def test_readded_title_with_new_manager_identifier_cancels_cleanup(ledger, media):
    download_hash = "a" * 40
    ledger.record_download(media, download_hash)
    ledger.enqueue(media)
    torrents = create_torrent_client(download_hash)
    worker = worker_for(ledger, torrents)
    worker.media_clients[media.app] = create_restored_media_client(
        media.app, media.provider_identifier
    )
    worker.process(media)
    torrents.delete.assert_not_called()
    worker.jellyfin.cleanup.assert_not_called()
    assert ledger.pending() == []


def test_readded_shared_owner_with_new_identifier_retains_torrent(ledger, media):
    owner = Media("radarr", 24, 5678, "Restored", "/data/media/movies/Old location")
    download_hash = "a" * 40
    ledger.record_download(owner, download_hash)
    ledger.record_download(media, download_hash)
    ledger.enqueue(media)
    torrents = create_torrent_client(download_hash)
    worker = worker_for(ledger, torrents)
    worker.media_clients[owner.app] = create_restored_media_client(
        owner.app, owner.provider_identifier
    )
    worker.run_pending()
    torrents.delete.assert_not_called()
    assert ledger.pending(now=10**12) == [media]


@pytest.mark.parametrize("app", ["radarr", "sonarr"])
def test_provider_lookup_matches_independently_of_manager_identifier(app):
    client = create_restored_media_client(app, 10331)
    assert not client.exists(31)
    assert client.exists(32)
    assert client.contains_provider(10331)
    assert not client.contains_provider(5678)


def test_provider_lookup_failure_keeps_cleanup_pending(ledger, media):
    ledger.record_download(media, "a" * 40)
    ledger.enqueue(media)
    torrents = create_torrent_client("a" * 40)
    worker = worker_for(ledger, torrents)
    media_client = Mock()
    media_client.exists.return_value = False
    media_client.contains_provider.side_effect = HttpFailure(503)
    worker.media_clients[media.app] = media_client
    worker.run_pending()
    torrents.delete.assert_not_called()
    assert ledger.pending(now=10**12) == [media]
