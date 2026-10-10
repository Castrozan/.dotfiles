import logging

from .domain import api_media, torrent_hash


def bootstrap(ledger, media_clients, torrents, filesystem):
    filesystem.assert_mounted()
    torrent_list = torrents.list()
    live_hashes = {value["hash"].lower() for value in torrent_list}
    media_list = []
    mapped = set()
    for app, client in media_clients.items():
        media_by_identifier = {
            value["id"]: api_media(app, value) for value in client.media()
        }
        media_list.extend(media_by_identifier.values())
        for record in client.history():
            media = media_by_identifier.get(
                record.get("movieId" if app == "radarr" else "seriesId")
            )
            if media is None or not record.get("downloadId"):
                continue
            try:
                download_hash = torrent_hash(record["downloadId"])
            except ValueError:
                continue
            if download_hash in live_hashes:
                ledger.record_download(media, download_hash)
                mapped.add(download_hash)
    unmapped = [value for value in torrent_list if value["hash"].lower() not in mapped]
    if unmapped:
        owners = {}
        for media in media_list:
            for inode in filesystem.linked_inodes(media.library_path):
                owners.setdefault(inode, set()).add(media)
        for torrent in unmapped:
            try:
                filesystem.validate_download(torrent["content_path"])
            except ValueError:
                continue
            associated = set()
            for inode in filesystem.linked_inodes(torrent["content_path"]):
                associated.update(owners.get(inode, set()))
            for media in associated:
                ledger.record_download(media, torrent["hash"])
                mapped.add(torrent["hash"].lower())
    logging.info(
        "Bootstrapped %s titles and %s existing torrent hashes",
        len(media_list),
        len(mapped),
    )
