import logging

from .domain import api_media, torrent_hash


def history_association(app, record, media_by_identifier, live_hashes):
    identity_field = {"radarr": "movieId", "sonarr": "seriesId"}[app]
    media = media_by_identifier.get(record.get(identity_field))
    if media is None:
        return None
    try:
        download_hash = torrent_hash(record.get("downloadId", ""))
    except ValueError:
        return None
    if download_hash not in live_hashes:
        return None
    return media, download_hash


def record_history(ledger, app, client, media_by_identifier, live_hashes):
    for record in client.history():
        association = history_association(app, record, media_by_identifier, live_hashes)
        if association is None:
            continue
        ledger.record_download(*association)
        yield association[1]


def inode_owners(media_list, filesystem):
    owners = {}
    for media in media_list:
        for inode in filesystem.linked_inodes(media.library_path):
            owners.setdefault(inode, set()).add(media)
    return owners


def record_torrent_links(ledger, torrent, owners, filesystem):
    try:
        filesystem.validate_download(torrent["content_path"])
    except ValueError:
        return False
    associated = set()
    for inode in filesystem.linked_inodes(torrent["content_path"]):
        associated.update(owners.get(inode, set()))
    for media in associated:
        ledger.record_download(media, torrent["hash"])
    return bool(associated)


def record_links(ledger, media_list, torrent_list, filesystem):
    owners = inode_owners(media_list, filesystem)
    return {
        value["hash"].lower()
        for value in torrent_list
        if record_torrent_links(ledger, value, owners, filesystem)
    }


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
        mapped.update(
            record_history(ledger, app, client, media_by_identifier, live_hashes)
        )
    mapped.update(record_links(ledger, media_list, torrent_list, filesystem))
    logging.info(
        "Bootstrapped %s titles and %s existing torrent hashes",
        len(media_list),
        len(mapped),
    )
