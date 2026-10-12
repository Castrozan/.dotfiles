from unittest.mock import Mock

from download_cleanup.worker import CleanupWorker


def worker_for(ledger, torrents):
    media_api = Mock()
    media_api.exists.return_value = False
    media_api.contains_provider.return_value = False
    filesystem = Mock(
        spec=[
            "assert_mounted",
            "library_exists",
            "download_exists",
            "validate_download",
        ]
    )
    filesystem.library_exists.return_value = False
    filesystem.download_exists.return_value = False
    jellyfin = Mock()
    return CleanupWorker(ledger, {"sonarr": media_api}, torrents, filesystem, jellyfin)
