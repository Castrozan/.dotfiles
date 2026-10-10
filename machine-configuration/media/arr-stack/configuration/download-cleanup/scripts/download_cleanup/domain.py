import re
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


def scoped_path(value, root, minimum_depth):
    path = PurePosixPath(value)
    if (
        ".." in path.parts
        or not path.is_relative_to(root)
        or len(path.parts) < minimum_depth
    ):
        raise ValueError(f"path outside permitted scope: {value}")
    return path


def torrent_hash(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", value
    ):
        raise ValueError("invalid torrent hash")
    return value.lower()


@dataclass(frozen=True)
class Media:
    app: str
    identifier: int
    provider_identifier: int
    title: str
    library_path: str

    def __post_init__(self):
        if self.app not in ("radarr", "sonarr"):
            raise ValueError("invalid media identity")
        validate_identifier(self.identifier)
        validate_identifier(self.provider_identifier)
        scoped_path(self.library_path, "/data/media", 5)

    @property
    def key(self):
        return self.app, self.identifier, self.provider_identifier, self.library_path

    def serialize(self):
        return asdict(self)


@dataclass(frozen=True)
class Event:
    kind: str
    media: Media
    download_hash: str | None = None


def api_media(app, value):
    return Media(
        app,
        value["id"],
        value["tmdbId" if app == "radarr" else "tvdbId"],
        value["title"],
        value["path"],
    )


def validate_identifier(identifier):
    if type(identifier) is not int or identifier <= 0:
        raise ValueError("invalid media identifier")


def event_kind(app, payload):
    event_type = payload.get("eventType")
    deletion_type = {"radarr": "MovieDelete", "sonarr": "SeriesDelete"}[app]
    if event_type == deletion_type:
        return "delete" if payload.get("deletedFiles") is True else None
    if event_type not in ("Grab", "Download"):
        return None
    if str(payload.get("downloadClientType", "")).lower() != "qbittorrent":
        return None
    return "download"


def native_media(app, payload):
    value = payload["movie" if app == "radarr" else "series"]
    return Media(
        app,
        value["id"],
        value["tmdbId" if app == "radarr" else "tvdbId"],
        value["title"],
        value["folderPath" if app == "radarr" else "path"],
    )


def parse_event(app, payload):
    kind = event_kind(app, payload)
    if kind is None:
        return None
    return Event(
        kind,
        native_media(app, payload),
        torrent_hash(payload["downloadId"]) if kind == "download" else None,
    )


def paths_overlap(left, right):
    return any((left == right, left in right.parents, right in left.parents))


def validate_download_paths(selected, unrelated):
    paths = [scoped_path(value, "/data/torrents", 4) for value in selected]
    for selected_path in paths:
        if any(
            paths_overlap(selected_path, PurePosixPath(value)) for value in unrelated
        ):
            raise ValueError("download path overlaps an unrelated torrent")
    return paths
