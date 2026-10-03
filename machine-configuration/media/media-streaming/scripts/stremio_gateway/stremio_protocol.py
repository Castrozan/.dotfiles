import re
from dataclasses import dataclass


STREAM_PATH = re.compile(
    r"^/prowlarr/stream/(?P<media_type>movie|series)/(?P<identifier>tt\d+(?::\d+:\d+)?)\.json$"
)


@dataclass(frozen=True)
class StreamRequest:
    media_type: str
    imdb_identifier: str
    season: int | None = None
    episode: int | None = None


def parse_stream_request(path: str) -> StreamRequest | None:
    match = STREAM_PATH.fullmatch(path)
    if match is None:
        return None
    identifier_parts = match.group("identifier").split(":")
    if _is_movie_identifier(match.group("media_type"), identifier_parts):
        return _movie_stream_request(identifier_parts)
    if _is_series_identifier(match.group("media_type"), identifier_parts):
        return _series_stream_request(identifier_parts)
    return None


def _movie_stream_request(identifier_parts):
    return StreamRequest("movie", identifier_parts[0])


def _series_stream_request(identifier_parts):
    return StreamRequest(
        "series",
        identifier_parts[0],
        int(identifier_parts[1]),
        int(identifier_parts[2]),
    )


def _is_movie_identifier(media_type, identifier_parts):
    return media_type == "movie" and len(identifier_parts) == 1


def _is_series_identifier(media_type, identifier_parts):
    return media_type == "series" and len(identifier_parts) == 3


def addon_manifest() -> dict:
    return {
        "id": "com.lucaszanoni.prowlarr-streams",
        "version": "1.0.0",
        "name": "Prowlarr Streams",
        "description": "Instant private movie and TV streams from Prowlarr",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"],
        "catalogs": [],
        "behaviorHints": {"p2p": True, "configurable": False},
    }
