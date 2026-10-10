import logging

from .domain import validate_download_paths


class CleanupWorker:
    def __init__(self, ledger, media_clients, torrents, filesystem, jellyfin):
        self.ledger = ledger
        self.media_clients = media_clients
        self.torrents = torrents
        self.filesystem = filesystem
        self.jellyfin = jellyfin

    def process(self, media):
        self.filesystem.assert_mounted()
        if self.media_clients[media.app].exists(media.identifier):
            self.ledger.cancel(media)
            logging.warning(
                "Cancelled cleanup for restored title %s/%s", media.app, media.title
            )
            return
        if self.filesystem.library_exists(media.library_path):
            raise RuntimeError("library deletion has not completed")
        records = self.ledger.downloads(media)
        hashes = {record[0] for record in records}
        for download_hash in hashes:
            for (
                app,
                identifier,
                provider_identifier,
                library_path,
            ) in self.ledger.owners(download_hash):
                if (app, identifier, provider_identifier, library_path) == media.key:
                    continue
                if self.media_clients[app].exists(
                    identifier
                ) or self.filesystem.library_exists(library_path):
                    raise RuntimeError("torrent is shared with retained media")
        torrents = self.torrents.list()
        selected = [value for value in torrents if value["hash"].lower() in hashes]
        unrelated = [
            value["content_path"]
            for value in torrents
            if value["hash"].lower() not in hashes
        ]
        paths = {value["content_path"] for value in selected} | {
            record[1] for record in records if record[1]
        }
        validate_download_paths(paths, unrelated)
        for path in paths:
            self.filesystem.validate_download(path)
        self.ledger.remember_paths(media, selected)
        if selected:
            self.torrents.delete(sorted(value["hash"].lower() for value in selected))
        if hashes.intersection(value["hash"].lower() for value in self.torrents.list()):
            raise RuntimeError("torrent deletion has not completed")
        if any(self.filesystem.download_exists(path) for path in paths):
            raise RuntimeError("download files remain after torrent deletion")
        self.jellyfin.refresh()
        self.ledger.complete(media)
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
