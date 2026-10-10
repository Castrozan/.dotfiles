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
        if (
            self.app not in ("radarr", "sonarr")
            or type(self.identifier) is not int
            or self.identifier <= 0
        ):
            raise ValueError("invalid media identity")
        if type(self.provider_identifier) is not int or self.provider_identifier <= 0:
            raise ValueError("invalid provider identity")
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


def parse_event(app, payload):
    event_type = payload.get("eventType")
    deletion_type = "MovieDelete" if app == "radarr" else "SeriesDelete"
    if event_type == deletion_type:
        if payload.get("deletedFiles") is not True:
            return None
        kind = "delete"
    elif event_type in ("Grab", "Download"):
        if str(payload.get("downloadClientType", "")).lower() != "qbittorrent":
            return None
        kind = "download"
    else:
        return None
    value = payload["movie" if app == "radarr" else "series"]
    media = Media(
        app,
        value["id"],
        value["tmdbId" if app == "radarr" else "tvdbId"],
        value["title"],
        value["folderPath" if app == "radarr" else "path"],
    )
    return Event(
        kind, media, torrent_hash(payload["downloadId"]) if kind == "download" else None
    )


def validate_download_paths(selected, unrelated):
    paths = [scoped_path(value, "/data/torrents", 4) for value in selected]
    for selected_path in paths:
        for value in unrelated:
            other_path = PurePosixPath(value)
            if (
                selected_path == other_path
                or selected_path in other_path.parents
                or other_path in selected_path.parents
            ):
                raise ValueError("download path overlaps an unrelated torrent")
    return paths
