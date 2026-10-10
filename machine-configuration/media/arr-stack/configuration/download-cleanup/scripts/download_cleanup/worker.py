import logging

from .domain import validate_download_paths


class CleanupWorker:
    def __init__(self, ledger, media_clients, torrents, filesystem, jellyfin):
        self.ledger = ledger
        self.media_clients = media_clients
        self.torrents = torrents
        self.filesystem = filesystem
        self.jellyfin = jellyfin

    def manager_contains_media(self, app, identifier, provider_identifier):
        client = self.media_clients[app]
        return client.exists(identifier) or client.contains_provider(
            provider_identifier
        )

    def retained_owner(self, owner):
        app, identifier, provider_identifier, library_path = owner
        return self.manager_contains_media(
            app, identifier, provider_identifier
        ) or self.filesystem.library_exists(library_path)

    def require_unshared(self, media, hashes):
        for download_hash in hashes:
            for owner in self.ledger.owners(download_hash):
                if owner == media.key:
                    continue
                if self.retained_owner(owner):
                    raise RuntimeError("torrent is shared with retained media")

    def selected_torrents(self, hashes):
        torrents = self.torrents.list()
        selected = [value for value in torrents if value["hash"].lower() in hashes]
        unrelated = [
            value["content_path"]
            for value in torrents
            if value["hash"].lower() not in hashes
        ]
        return selected, unrelated

    def download_paths(self, records, selected, unrelated):
        paths = {value["content_path"] for value in selected} | {
            record[1] for record in records if record[1]
        }
        validate_download_paths(paths, unrelated)
        for path in paths:
            self.filesystem.validate_download(path)
        return paths

    def remove_torrents(self, media, selected):
        self.ledger.remember_paths(media, selected)
        if selected:
            self.torrents.delete(sorted(value["hash"].lower() for value in selected))

    def verify_removal(self, hashes, paths):
        if hashes.intersection(value["hash"].lower() for value in self.torrents.list()):
            raise RuntimeError("torrent deletion has not completed")
        if any(self.filesystem.download_exists(path) for path in paths):
            raise RuntimeError("download files remain after torrent deletion")

    def process(self, media):
        self.filesystem.assert_mounted()
        if self.manager_contains_media(
            media.app, media.identifier, media.provider_identifier
        ):
            self.ledger.cancel(media)
            logging.warning(
                "Cancelled cleanup for restored title %s/%s", media.app, media.title
            )
            return
        if self.filesystem.library_exists(media.library_path):
            raise RuntimeError("library deletion has not completed")
        revision = self.ledger.revision(media)
        records = self.ledger.downloads(media)
        hashes = {record[0] for record in records}
        self.require_unshared(media, hashes)
        selected, unrelated = self.selected_torrents(hashes)
        paths = self.download_paths(records, selected, unrelated)
        self.remove_torrents(media, selected)
        self.verify_removal(hashes, paths)
        self.jellyfin.cleanup(media)
        if self.ledger.complete(media, revision):
            logging.info(
                "Cleaned %s/%s: %s torrent associations",
                media.app,
                media.title,
                len(hashes),
            )

    def run_pending(self):
        for media in self.ledger.pending():
            try:
                self.process(media)
            except Exception:
                self.ledger.retry(media)
                logging.exception("Cleanup pending for %s/%s", media.app, media.title)
