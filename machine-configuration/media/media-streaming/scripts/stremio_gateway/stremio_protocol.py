import re
import urllib.parse
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
    if match.group("media_type") == "movie" and len(identifier_parts) == 1:
        return StreamRequest("movie", identifier_parts[0])
    if match.group("media_type") == "series" and len(identifier_parts) == 3:
        return StreamRequest(
            "series",
            identifier_parts[0],
            int(identifier_parts[1]),
            int(identifier_parts[2]),
        )
    return None


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


def setup_url(web_url: str, streaming_server_url: str, addon_manifest_url: str) -> str:
    route_query = urllib.parse.urlencode(
        {
            "addon": addon_manifest_url,
            "streamingServerUrl": streaming_server_url,
        }
    )
    return f"{web_url.rstrip('/')}/#/addons?{route_query}"


def setup_url_for_request_origin(
    request_origin: str,
    tailnet_web_url: str,
    tailnet_streaming_server_url: str,
) -> str:
    normalized_origin = request_origin.rstrip("/")
    normalized_tailnet_web_url = tailnet_web_url.rstrip("/")
    streaming_server_url = (
        tailnet_streaming_server_url
        if normalized_origin == normalized_tailnet_web_url
        else f"{normalized_origin}/server/"
    )
    return setup_url(
        normalized_origin,
        streaming_server_url,
        f"{normalized_origin}/prowlarr/manifest.json",
    )
